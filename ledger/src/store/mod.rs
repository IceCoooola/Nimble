use super::{Block, Handle, MetaBlock, NimbleDigest, NimbleHashTrait, Receipt};
use crate::errors::LedgerStoreError;
use async_trait::async_trait;
use std::collections::HashMap;

pub mod in_memory;
pub mod mongodb_cosmos;

#[derive(Debug, Default, Clone)]
pub struct LedgerEntry {
  pub block: Block,
  pub metablock: MetaBlock,
  pub receipt: Receipt,
}

#[derive(Debug, Default, Clone)]
pub struct LedgerView {
  pub view_tail_metablock: MetaBlock,
  pub view_tail_hash: NimbleDigest,
  pub ledger_tail_map: HashMap<NimbleDigest, (NimbleDigest, usize)>,
}

#[async_trait]
pub trait LedgerStore {
  async fn create_ledger(
    &self,
    block: &Block,
  ) -> Result<(Handle, MetaBlock, NimbleDigest), LedgerStoreError>;
  async fn append_ledger(
    // TODO: should self be mutable?
    &self,
    handle: &Handle,
    block: &Block,
    cond: &NimbleDigest,
  ) -> Result<(MetaBlock, NimbleDigest), LedgerStoreError>;
  async fn attach_ledger_receipt(
    &self,
    handle: &Handle,
    metablock: &MetaBlock,
    receipt: &Receipt,
  ) -> Result<(), LedgerStoreError>;
  async fn read_ledger_tail(&self, handle: &Handle) -> Result<LedgerEntry, LedgerStoreError>;
  async fn read_ledger_by_index(
    &self,
    handle: &Handle,
    idx: usize,
  ) -> Result<LedgerEntry, LedgerStoreError>;
  async fn append_view_ledger(&self, block: &Block) -> Result<LedgerView, LedgerStoreError>;
  async fn attach_view_ledger_receipt(
    &self,
    metablock: &MetaBlock,
    receipt: &Receipt,
  ) -> Result<(), LedgerStoreError>;
  async fn read_view_ledger_tail(&self) -> Result<LedgerEntry, LedgerStoreError>;
  async fn read_view_ledger_by_index(&self, idx: usize) -> Result<LedgerEntry, LedgerStoreError>;

  async fn reset_store(&self) -> Result<(), LedgerStoreError>; // only used for testing
}

#[cfg(test)]
mod tests {
  use crate::store::in_memory::InMemoryLedgerStore;
  use crate::store::mongodb_cosmos::MongoCosmosLedgerStore;
  use crate::store::LedgerStore;
  use crate::Block;
  use crate::NimbleDigest;
  use std::collections::HashMap;

  pub async fn check_store_creation_and_operations(state: &dyn LedgerStore) {
    let initial_value: Vec<u8> = vec![
      1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
      1, 2,
    ];

    let block = Block::new(&initial_value);

    let (handle, _, _) = state
      .create_ledger(&block)
      .await
      .expect("failed create ledger");

    let res = state.read_ledger_tail(&handle).await;
    assert!(res.is_ok());

    let current_data = res.unwrap();
    assert_eq!(current_data.block.block, initial_value);

    let new_value_appended: Vec<u8> = vec![
      2, 3, 4, 5, 6, 7, 8, 9, 10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1,
      2, 1,
    ];

    let new_block = Block::new(&new_value_appended);

    let res = state
      .append_ledger(&handle, &new_block, &NimbleDigest::default())
      .await;
    assert!(res.is_ok());

    let res = state.read_ledger_tail(&handle).await;
    assert!(res.is_ok());

    let current_tail = res.unwrap();
    assert_eq!(current_tail.block.block, new_value_appended);

    let res = state.read_ledger_by_index(&handle, 0).await;
    assert!(res.is_ok());

    let data_at_index = res.unwrap();
    assert_eq!(data_at_index.block.block, initial_value);

    let res = state.reset_store().await;
    assert!(res.is_ok());
  }

  #[tokio::test]
  pub async fn check_in_memory_store() {
    let state = InMemoryLedgerStore::new();
    check_store_creation_and_operations(&state).await;
  }

  #[tokio::test]
  pub async fn check_mongo_cosmos_store() {
    if std::env::var_os("COSMOS_URL").is_none() {
      // The right env variable is not available so let's skip tests
      return;
    }
    let mut args = HashMap::<String, String>::new();
    args.insert(
      String::from("COSMOS_URL"),
      std::env::var_os("COSMOS_URL")
        .unwrap()
        .into_string()
        .unwrap(),
    );

    let state = MongoCosmosLedgerStore::new(&args).await.unwrap();
    check_store_creation_and_operations(&state).await;
  }
}
