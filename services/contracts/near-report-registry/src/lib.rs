use near_sdk::store::{IterableSet, LookupMap};
use near_sdk::{env, near, require, AccountId, PanicOnDefault};

const EVENT_STANDARD: &str = "triplees_report_registry";
const EVENT_VERSION: &str = "1.0.0";

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct TripleESReportRegistry {
    owner_id: AccountId,
    reviewers: IterableSet<AccountId>,
    commitments: LookupMap<String, ReportCommitment>,
}

#[near(serializers = [json, borsh])]
#[derive(Clone)]
#[serde(rename_all = "camelCase")]
pub struct ReportCommitment {
    pub investigation_id: String,
    pub report_version: u32,
    pub report_digest: String,
    pub metadata_digest: Option<String>,
    pub submitter: AccountId,
    pub committed_at_ns: u64,
}

#[near]
impl TripleESReportRegistry {
    #[init]
    pub fn new(owner_id: String) -> Self {
        let owner_id = owner_id.parse::<AccountId>().unwrap_or_else(|_| env::panic_str("Invalid owner account ID"));
        require!(owner_id == env::predecessor_account_id(), "Owner must initialize contract");
        let mut reviewers = IterableSet::new(&b"reviewers"[..]);
        reviewers.insert(owner_id.clone());
        Self {
            owner_id,
            reviewers,
            commitments: LookupMap::new(&b"commitments"[..]),
        }
    }

    pub fn grant_reviewer(&mut self, account_id: AccountId) {
        self.assert_owner();
        let changed = self.reviewers.insert(account_id.clone());
        self.emit_permission_event(&account_id, true, changed);
    }

    pub fn revoke_reviewer(&mut self, account_id: AccountId) {
        self.assert_owner();
        let changed = self.reviewers.remove(&account_id);
        self.emit_permission_event(&account_id, false, changed);
    }

    pub fn is_reviewer(&self, account_id: AccountId) -> bool {
        self.reviewers.contains(&account_id)
    }

    pub fn commit_report(
        &mut self,
        investigation_id: String,
        report_version: u32,
        report_digest: String,
        metadata_digest: Option<String>,
    ) -> ReportCommitment {
        let submitter = env::predecessor_account_id();
        require!(self.reviewers.contains(&submitter), "Reviewer permission required");
        require!(valid_identifier(&investigation_id), "Invalid investigation ID");
        require!(report_version > 0, "Report version must be greater than zero");
        require!(valid_digest(&report_digest), "Invalid report digest");
        if let Some(digest) = &metadata_digest {
            require!(valid_digest(digest), "Invalid metadata digest");
        }

        let key = commitment_key(&investigation_id, report_version);
        require!(!self.commitments.contains_key(&key), "Report version already committed");

        let commitment = ReportCommitment {
            investigation_id,
            report_version,
            report_digest: report_digest.to_ascii_lowercase(),
            metadata_digest: metadata_digest.map(|value| value.to_ascii_lowercase()),
            submitter,
            committed_at_ns: env::block_timestamp(),
        };
        self.commitments.insert(key, commitment.clone());
        emit_event(
            "report_committed",
            near_sdk::serde_json::json!({
                "investigation_id": commitment.investigation_id,
                "report_version": commitment.report_version,
                "report_digest": commitment.report_digest,
                "metadata_digest": commitment.metadata_digest,
                "submitter": commitment.submitter,
                "committed_at_ns": commitment.committed_at_ns,
            }),
        );
        commitment
    }

    pub fn verify_report(
        &self,
        investigation_id: String,
        report_version: u32,
    ) -> Option<ReportCommitment> {
        self.commitments
            .get(&commitment_key(&investigation_id, report_version))
            .cloned()
    }

    pub fn owner(&self) -> AccountId {
        self.owner_id.clone()
    }

    fn assert_owner(&self) {
        require!(env::predecessor_account_id() == self.owner_id, "Only owner can manage reviewers");
    }

    fn emit_permission_event(&self, account_id: &AccountId, allowed: bool, changed: bool) {
        emit_event(
            "reviewer_permission_changed",
            near_sdk::serde_json::json!({
                "account_id": account_id,
                "allowed": allowed,
                "changed": changed,
            }),
        );
    }
}

fn commitment_key(investigation_id: &str, report_version: u32) -> String {
    format!("{investigation_id}#{report_version}")
}

fn valid_identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 128
        && value.bytes().all(|byte| {
            byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.')
        })
}

fn valid_digest(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn emit_event(name: &str, data: near_sdk::serde_json::Value) {
    let event = near_sdk::serde_json::json!({
        "standard": EVENT_STANDARD,
        "version": EVENT_VERSION,
        "event": name,
        "data": [data],
    });
    env::log_str(&format!("EVENT_JSON:{event}"));
}

#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::test_utils::{accounts, get_logs, VMContextBuilder};
    use near_sdk::testing_env;

    fn set_predecessor(account_id: AccountId) {
        testing_env!(VMContextBuilder::new().predecessor_account_id(account_id).build());
    }

    fn new_registry() -> (TripleESReportRegistry, AccountId, AccountId) {
        let owner = accounts(0);
        let reviewer = accounts(1);
        set_predecessor(owner.clone());
        let registry = TripleESReportRegistry::new(owner.to_string());
        (registry, owner, reviewer)
    }

    #[test]
    fn reviewer_can_commit_and_publicly_verify_report() {
        let (mut registry, owner, _) = new_registry();
        set_predecessor(owner.clone());
        let commitment = registry.commit_report(
            "INV-42".to_string(),
            1,
            "AB".repeat(32),
            Some("CD".repeat(32)),
        );

        assert_eq!(commitment.report_digest, "ab".repeat(32));
        assert_eq!(commitment.metadata_digest, Some("cd".repeat(32)));
        assert_eq!(commitment.submitter, owner);
        assert_eq!(registry.verify_report("INV-42".to_string(), 1).unwrap().report_version, 1);
        assert!(get_logs().iter().any(|line| line.contains("EVENT_JSON:") && line.contains("report_committed")));
    }

    #[test]
    #[should_panic(expected = "Reviewer permission required")]
    fn unauthorized_account_cannot_commit() {
        let (mut registry, _, reviewer) = new_registry();
        set_predecessor(reviewer);
        registry.commit_report("INV-42".to_string(), 1, "ab".repeat(32), None);
    }

    #[test]
    #[should_panic(expected = "Report version already committed")]
    fn duplicate_report_version_is_rejected() {
        let (mut registry, owner, _) = new_registry();
        set_predecessor(owner);
        registry.commit_report("INV-42".to_string(), 1, "ab".repeat(32), None);
        registry.commit_report("INV-42".to_string(), 1, "cd".repeat(32), None);
    }

    #[test]
    fn a_new_report_version_is_a_distinct_commitment() {
        let (mut registry, owner, _) = new_registry();
        set_predecessor(owner);
        registry.commit_report("INV-42".to_string(), 1, "ab".repeat(32), None);
        registry.commit_report("INV-42".to_string(), 2, "cd".repeat(32), None);
        assert_eq!(registry.verify_report("INV-42".to_string(), 2).unwrap().report_digest, "cd".repeat(32));
    }

    #[test]
    fn missing_investigation_version_returns_none() {
        let (registry, _, _) = new_registry();
        assert!(registry.verify_report("INV-MISSING".to_string(), 1).is_none());
    }

    #[test]
    #[should_panic(expected = "Invalid report digest")]
    fn malformed_digest_is_rejected() {
        let (mut registry, owner, _) = new_registry();
        set_predecessor(owner);
        registry.commit_report("INV-42".to_string(), 1, "not-a-digest".to_string(), None);
    }

    #[test]
    fn owner_can_grant_and_revoke_reviewer_permissions() {
        let (mut registry, owner, reviewer) = new_registry();
        set_predecessor(owner.clone());
        registry.grant_reviewer(reviewer.clone());
        assert!(registry.is_reviewer(reviewer.clone()));
        registry.revoke_reviewer(reviewer.clone());
        assert!(!registry.is_reviewer(reviewer));
        assert!(get_logs().iter().any(|line| line.contains("reviewer_permission_changed")));
    }

    #[test]
    #[should_panic(expected = "Only owner can manage reviewers")]
    fn non_owner_cannot_change_reviewer_permissions() {
        let (mut registry, _, reviewer) = new_registry();
        set_predecessor(reviewer.clone());
        registry.grant_reviewer(reviewer);
    }
}