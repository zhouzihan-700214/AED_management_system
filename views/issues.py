from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import re

import pandas as pd
import streamlit as st

from services.issue_service import (
    add_issue_progress_update,
    assign_issue,
    get_attachments_for_issue,
    get_history_for_issue,
    get_open_issue_count,
    get_resolution_submissions_for_issue,
    is_closed_status,
    load_issue_records,
    resolve_attachment_path,
    start_issue_work,
    submit_issue_resolution,
    verify_issue_resolution,
    TEST_RESULT_OPTIONS,
)

from ui.components import page_header
from utils.text_utils import clean_text


STATUS_HELP = {
    "Reported": "The Issue has been submitted and is waiting for review and assignment.",
    "Assigned": "A person has been assigned to handle the Issue.",
    "In Progress": "Work has started and progress updates can be recorded.",
    "Pending Verification": (
        "Resolution details and evidence were submitted and are waiting for review."
    ),
    "Reopened": "Verification failed or more work is required.",
    "Closed": "The submitted resolution was verified and approved.",
}


def _safe_key(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", clean_text(value)) or "issue"


def _parse_due_date(value: object) -> date | None:
    text = clean_text(value)
    if not text:
        return None

    for date_format in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def _legacy_photo_paths(
    photo_paths_text: str,
    issue_csv_file: str | Path,
) -> list[Path]:
    paths: list[Path] = []
    for item in clean_text(photo_paths_text).split(";"):
        item = clean_text(item)
        if item:
            paths.append(resolve_attachment_path(issue_csv_file, item))
    return paths


def _render_evidence(
    row: pd.Series,
    issue_csv_file: str | Path,
) -> None:
    issue_id = clean_text(row.get("Issue ID"))
    attachments = get_attachments_for_issue(issue_csv_file, issue_id)

    evidence: list[tuple[Path, str, str]] = []
    if not attachments.empty:
        for _, attachment in attachments.iterrows():
            path = resolve_attachment_path(
                issue_csv_file,
                clean_text(attachment.get("File Path")),
            )
            evidence.append(
                (
                    path,
                    clean_text(attachment.get("Caption")) or path.name,
                    clean_text(attachment.get("Stage")) or "Evidence",
                )
            )
    else:
        for path in _legacy_photo_paths(
            clean_text(row.get("Photo Paths")), issue_csv_file
        ):
            evidence.append((path, path.name, "Legacy Report"))

    if not evidence:
        st.caption("No photos were uploaded.")
        return

    visible = [item for item in evidence if item[0].exists()]
    if visible:
        columns = st.columns(min(len(visible), 3))
        for index, (path, caption, stage) in enumerate(visible):
            with columns[index % len(columns)]:
                st.image(
                    str(path),
                    caption=f"{stage}: {caption}",
                    width="stretch",
                )

    missing = [path.name for path, _, _ in evidence if not path.exists()]
    if missing:
        st.warning(
            "These saved photo files could not be found: " + ", ".join(missing)
        )


def _render_history(issue_id: str, issue_csv_file: str | Path) -> None:
    history = get_history_for_issue(issue_csv_file, issue_id)
    if history.empty:
        st.caption(
            "No structured activity history is available for this legacy Issue."
        )
        return

    for _, event in history.iterrows():
        from_status = clean_text(event.get("From Status")) or "—"
        to_status = clean_text(event.get("To Status")) or "—"
        st.markdown(
            f"**{clean_text(event.get('Action At')) or 'Unknown time'} — "
            f"{clean_text(event.get('Action')) or 'Updated'}**"
        )
        st.caption(
            f"{from_status} → {to_status} · "
            f"By {clean_text(event.get('Action By')) or 'Unknown'}"
        )
        comments = clean_text(event.get("Comments"))
        if comments:
            st.write(comments)
        st.divider()



def _render_resolution_submissions(
    issue_id: str,
    issue_csv_file: str | Path,
) -> None:
    submissions = get_resolution_submissions_for_issue(
        issue_csv_file,
        issue_id,
    )
    if submissions.empty:
        st.caption("No resolution has been submitted yet.")
        return

    for _, submission in submissions.iterrows():
        attempt = clean_text(submission.get("Attempt Number")) or "—"
        submitted_by = clean_text(submission.get("Submitted By")) or "—"
        submitted_at = clean_text(submission.get("Submitted At")) or "—"
        verification = (
            clean_text(submission.get("Verification Result")) or "Pending"
        )

        with st.container(border=True):
            header_left, header_right = st.columns([3, 1])
            with header_left:
                st.markdown(f"**Resolution Attempt {attempt}**")
                st.caption(f"Submitted by {submitted_by} at {submitted_at}")
            with header_right:
                st.markdown(f"**Verification:** {verification}")

            st.markdown("**Action Taken**")
            st.write(clean_text(submission.get("Action Taken")) or "—")

            root_cause = clean_text(submission.get("Root Cause"))
            parts_replaced = clean_text(submission.get("Parts Replaced"))
            if root_cause:
                st.markdown(f"**Root Cause:** {root_cause}")
            if parts_replaced:
                st.markdown(f"**Parts Replaced:** {parts_replaced}")

            test_left, test_right = st.columns([3, 1])
            with test_left:
                st.markdown("**Test Performed**")
                st.write(clean_text(submission.get("Test Performed")) or "—")
            with test_right:
                st.markdown(
                    "**Test Result:** "
                    + (clean_text(submission.get("Test Result")) or "—")
                )

            st.markdown("**Resolution Notes**")
            st.write(clean_text(submission.get("Resolution Notes")) or "—")

            verification_notes = clean_text(
                submission.get("Verification Notes")
            )
            verified_by = clean_text(submission.get("Verified By"))
            verified_at = clean_text(submission.get("Verified At"))
            if verification_notes or verified_by or verified_at:
                st.markdown("**Verification Details**")
                st.write(
                    f"Verified By: {verified_by or '—'} | "
                    f"Verified At: {verified_at or '—'}"
                )
                if verification_notes:
                    st.write(verification_notes)

def build_issue_copy_text(row: pd.Series) -> str:
    lines = [
        "AED ISSUE REPORT",
        f"Issue ID: {clean_text(row.get('Issue ID')) or '—'}",
        f"Status: {clean_text(row.get('Status')) or 'Reported'}",
        f"Priority: {clean_text(row.get('Priority')) or 'Not set'}",
        f"Reported At: {clean_text(row.get('Reported At')) or '—'}",
        f"Reported By: {clean_text(row.get('Reported By')) or clean_text(row.get('Technician')) or '—'}",
        "",
        "AED INFORMATION",
        f"Serial Number: {clean_text(row.get('Serial Number')) or '—'}",
        f"Model: {clean_text(row.get('Model')) or '—'}",
        f"Location: {clean_text(row.get('Location')) or '—'}",
        f"Postal Code: {clean_text(row.get('Postal Code')) or '—'}",
        f"Lift Lobby: {clean_text(row.get('Lift Lobby')) or '—'}",
        "",
        "ISSUE DETAILS",
        f"Issue Type: {clean_text(row.get('Issue Type')) or '—'}",
        f"Description: {clean_text(row.get('Detailed Description')) or '—'}",
        "",
        "REVIEW AND ASSIGNMENT",
        f"Reviewed By: {clean_text(row.get('Reviewed By')) or '—'}",
        f"Current Assignee: {clean_text(row.get('Current Assignee')) or '—'}",
        f"Due Date: {clean_text(row.get('Due Date')) or '—'}",
        f"Started By: {clean_text(row.get('Started By')) or '—'}",
        f"Started At: {clean_text(row.get('Started At')) or '—'}",
    ]
    return "\n".join(lines)


def _show_action_success() -> None:
    message = st.session_state.pop("issue_action_success_message", "")
    if message:
        st.success(message)


def _save_success(message: str) -> None:
    st.session_state["issue_action_success_message"] = message
    st.rerun()


def _render_assignment_form(
    row: pd.Series,
    issue_csv_file: str | Path,
    *,
    key_prefix: str,
    title: str,
) -> None:
    issue_id = clean_text(row.get("Issue ID"))
    existing_due_date = _parse_due_date(row.get("Due Date"))
    current_assignee = clean_text(row.get("Current Assignee"))

    st.subheader(title)
    st.caption(
        "The reviewer records the decision and assigns responsibility. "
        "The reviewer and assignee may be different people."
    )

    with st.form(f"{key_prefix}_assignment_form"):
        left, right = st.columns(2)
        with left:
            reviewed_by = st.text_input(
                "Reviewed / Assigned By *",
                key=f"{key_prefix}_reviewed_by",
                help="The administrator or supervisor who reviewed and assigned the Issue.",
            )
            assigned_to = st.text_input(
                "Assigned To *",
                value=current_assignee,
                key=f"{key_prefix}_assigned_to",
                help="The person responsible for carrying out the work.",
            )
        with right:
            set_due_date = st.checkbox(
                "Set a due date",
                value=existing_due_date is not None,
                key=f"{key_prefix}_set_due_date",
            )
            due_date_value = st.date_input(
                "Due Date",
                value=existing_due_date or date.today(),
                disabled=not set_due_date,
                key=f"{key_prefix}_due_date",
            )

        review_notes = st.text_area(
            "Review Notes",
            value=clean_text(row.get("Review Notes")),
            placeholder="Confirm what was reviewed and any important observations.",
            key=f"{key_prefix}_review_notes",
        )
        assignment_notes = st.text_area(
            "Assignment Instructions",
            value=clean_text(row.get("Assignment Notes")),
            placeholder="Describe what the assignee should check, repair, or prepare.",
            key=f"{key_prefix}_assignment_notes",
        )

        submitted = st.form_submit_button(
            "Save Assignment",
            type="primary",
            width="stretch",
        )

    if not submitted:
        return

    try:
        assign_issue(
            issue_csv_file,
            issue_id=issue_id,
            reviewed_by=reviewed_by,
            assigned_to=assigned_to,
            due_date=due_date_value.isoformat() if set_due_date else "",
            review_notes=review_notes,
            assignment_notes=assignment_notes,
        )
    except Exception as error:
        st.error(f"Failed to save the assignment: {error}")
        return

    _save_success(f"{issue_id} was assigned to {clean_text(assigned_to)}.")


def _render_start_work_form(
    row: pd.Series,
    issue_csv_file: str | Path,
    *,
    key_prefix: str,
) -> None:
    issue_id = clean_text(row.get("Issue ID"))
    current_assignee = clean_text(row.get("Current Assignee"))

    st.subheader("Start Work")
    st.caption(
        "Starting work changes the Issue to In Progress and records who began the work."
    )

    with st.form(f"{key_prefix}_start_work_form"):
        started_by = st.text_input(
            "Started By *",
            value=current_assignee,
            key=f"{key_prefix}_started_by",
        )
        work_notes = st.text_area(
            "Starting Notes",
            placeholder="Optional: record the initial inspection or planned action.",
            key=f"{key_prefix}_starting_notes",
        )
        submitted = st.form_submit_button(
            "Start Work",
            type="primary",
            width="stretch",
        )

    if not submitted:
        return

    try:
        start_issue_work(
            issue_csv_file,
            issue_id=issue_id,
            started_by=started_by,
            work_notes=work_notes,
        )
    except Exception as error:
        st.error(f"Failed to start work: {error}")
        return

    _save_success(f"Work on {issue_id} is now In Progress.")


def _render_progress_update_form(
    row: pd.Series,
    issue_csv_file: str | Path,
    *,
    key_prefix: str,
) -> None:
    issue_id = clean_text(row.get("Issue ID"))
    default_actor = (
        clean_text(row.get("Current Assignee"))
        or clean_text(row.get("Started By"))
    )

    st.subheader("Add Progress Update")
    st.caption(
        "Use progress updates for site findings, parts required, delays, and work completed so far."
    )

    with st.form(f"{key_prefix}_progress_form"):
        updated_by = st.text_input(
            "Updated By *",
            value=default_actor,
            key=f"{key_prefix}_progress_by",
        )
        progress_notes = st.text_area(
            "Progress Notes *",
            placeholder=(
                "Example: Reached site, confirmed cabinet alarm fault, and requested a replacement switch."
            ),
            height=130,
            key=f"{key_prefix}_progress_notes",
        )
        submitted = st.form_submit_button(
            "Save Progress Update",
            width="stretch",
        )

    if not submitted:
        return

    try:
        add_issue_progress_update(
            issue_csv_file,
            issue_id=issue_id,
            updated_by=updated_by,
            progress_notes=progress_notes,
        )
    except Exception as error:
        st.error(f"Failed to save the progress update: {error}")
        return

    _save_success(f"Progress was added to {issue_id}.")



def _render_resolution_submission_form(
    row: pd.Series,
    issue_csv_file: str | Path,
    *,
    key_prefix: str,
) -> None:
    issue_id = clean_text(row.get("Issue ID"))
    default_actor = (
        clean_text(row.get("Current Assignee"))
        or clean_text(row.get("Started By"))
    )

    st.subheader("Submit Resolution")
    st.caption(
        "Submit what was done, how the result was tested, and completion photos. "
        "This does not close the Issue; it sends the Issue for verification."
    )

    with st.form(f"{key_prefix}_resolution_form", clear_on_submit=False):
        submitted_by = st.text_input(
            "Submitted By *",
            value=default_actor,
            key=f"{key_prefix}_resolution_by",
        )
        action_taken = st.text_area(
            "Action Taken *",
            placeholder=(
                "Describe the repair, replacement, correction, or other action completed."
            ),
            height=120,
            key=f"{key_prefix}_action_taken",
        )

        detail_left, detail_right = st.columns(2)
        with detail_left:
            root_cause = st.text_area(
                "Root Cause (optional)",
                placeholder="Describe the confirmed cause, if known.",
                key=f"{key_prefix}_root_cause",
            )
        with detail_right:
            parts_replaced = st.text_area(
                "Parts Replaced (optional)",
                placeholder="List replaced parts, or leave blank.",
                key=f"{key_prefix}_parts_replaced",
            )

        test_performed = st.text_area(
            "Test Performed *",
            placeholder=(
                "Describe how you checked that the Issue was resolved, including the test steps."
            ),
            height=110,
            key=f"{key_prefix}_test_performed",
        )
        test_result = st.selectbox(
            "Test Result *",
            options=TEST_RESULT_OPTIONS,
            key=f"{key_prefix}_test_result",
            help=(
                "Choose Pass when the functional check succeeded. Choose Not Applicable "
                "only when no functional test applies, and explain why in the notes."
            ),
        )
        resolution_notes = st.text_area(
            "Resolution Notes *",
            placeholder=(
                "Summarise the final condition and any follow-up, monitoring, or limitation."
            ),
            height=120,
            key=f"{key_prefix}_resolution_notes",
        )
        completion_photos = st.file_uploader(
            "Completion Photos *",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key=f"{key_prefix}_completion_photos",
            help=(
                "Upload at least one clear photo showing the repaired area, final condition, "
                "or test evidence."
            ),
        )
        resolution_confirmed = st.checkbox(
            "I confirm this resolution is ready for verification. The unit marker will change to the Pending Verification colour.",
            key=f"{key_prefix}_resolution_confirmed",
        )

        submitted = st.form_submit_button(
            "Submit for Verification",
            type="primary",
            width="stretch",
        )

    if not submitted:
        return
    if not resolution_confirmed:
        st.error("Confirm the resolution and resulting marker status before submitting.")
        return

    try:
        submission_id = submit_issue_resolution(
            issue_csv_file,
            issue_id=issue_id,
            submitted_by=submitted_by,
            action_taken=action_taken,
            root_cause=root_cause,
            parts_replaced=parts_replaced,
            test_performed=test_performed,
            test_result=test_result,
            resolution_notes=resolution_notes,
            uploaded_files=completion_photos or [],
        )
    except Exception as error:
        st.error(f"Failed to submit the resolution: {error}")
        return

    _save_success(
        f"Resolution {submission_id} was submitted. {issue_id} is now Pending Verification and the unit marker follows that colour."
    )


def _render_verification_form(
    row: pd.Series,
    issue_csv_file: str | Path,
    *,
    key_prefix: str,
) -> None:
    issue_id = clean_text(row.get("Issue ID"))
    latest_submission_id = clean_text(row.get("Latest Submission ID"))
    submissions = get_resolution_submissions_for_issue(
        issue_csv_file,
        issue_id,
    )

    if submissions.empty or not latest_submission_id:
        st.error(
            "This Issue is Pending Verification, but no linked resolution submission "
            "could be found."
        )
        return

    matching = submissions.loc[
        submissions["Submission ID"]
        .astype(str)
        .str.strip()
        .eq(latest_submission_id)
    ]
    if matching.empty:
        st.error(
            f"The latest resolution submission ({latest_submission_id}) could not be found."
        )
        return

    submission = matching.iloc[0]
    submitted_by = clean_text(submission.get("Submitted By")) or "—"
    attempt = clean_text(submission.get("Attempt Number")) or "—"

    st.subheader("Verify Submitted Resolution")
    st.caption(
        "Review the work description, test result, and completion photos. "
        "Approval closes the Issue; rejection returns it for more work."
    )

    with st.container(border=True):
        st.markdown(
            f"**Resolution Attempt {attempt}** · "
            f"Submitted by {submitted_by} · "
            f"{clean_text(submission.get('Submitted At')) or 'Unknown time'}"
        )
        st.markdown("**Action Taken**")
        st.write(clean_text(submission.get("Action Taken")) or "—")

        detail_left, detail_right = st.columns(2)
        with detail_left:
            st.markdown("**Test Performed**")
            st.write(clean_text(submission.get("Test Performed")) or "—")
        with detail_right:
            st.markdown("**Test Result**")
            st.write(clean_text(submission.get("Test Result")) or "—")

        st.markdown("**Resolution Notes**")
        st.write(clean_text(submission.get("Resolution Notes")) or "—")

        attachments = get_attachments_for_issue(issue_csv_file, issue_id)
        if not attachments.empty:
            attachments = attachments.loc[
                attachments["Submission ID"]
                .astype(str)
                .str.strip()
                .eq(latest_submission_id)
            ]

        if attachments.empty:
            st.error(
                "No completion photo is linked to this resolution submission. "
                "Do not approve it until the evidence problem is corrected."
            )
        else:
            st.markdown("**Completion Photos**")
            valid_photos: list[tuple[Path, str]] = []
            missing_names: list[str] = []
            for _, attachment in attachments.iterrows():
                photo_path = resolve_attachment_path(
                    issue_csv_file,
                    clean_text(attachment.get("File Path")),
                )
                if photo_path.exists():
                    valid_photos.append(
                        (
                            photo_path,
                            clean_text(attachment.get("Caption")) or photo_path.name,
                        )
                    )
                else:
                    missing_names.append(photo_path.name)

            if valid_photos:
                photo_columns = st.columns(min(len(valid_photos), 3))
                for index, (photo_path, caption) in enumerate(valid_photos):
                    with photo_columns[index % len(photo_columns)]:
                        st.image(
                            str(photo_path),
                            caption=caption,
                            width="stretch",
                        )
            if missing_names:
                st.warning(
                    "Some saved completion photos could not be found: "
                    + ", ".join(missing_names)
                )

    with st.form(f"{key_prefix}_verification_form"):
        verified_by = st.text_input(
            "Verified By *",
            key=f"{key_prefix}_verified_by",
            help="The administrator or supervisor making the final decision.",
        )
        decision = st.radio(
            "Verification Decision *",
            options=["Approve and Close", "Reject and Reopen"],
            key=f"{key_prefix}_verification_decision",
            help=(
                "Approve only when the written result and photos provide sufficient "
                "evidence. Reject when more work, clearer evidence, or another test is needed."
            ),
        )
        verification_notes = st.text_area(
            "Verification Notes / Rejection Reason *",
            placeholder=(
                "State what was checked and why the submission is accepted, or explain "
                "exactly what must be corrected before resubmission."
            ),
            height=130,
            key=f"{key_prefix}_verification_notes",
        )
        evidence_confirmed = st.checkbox(
            "I reviewed the resolution details, test result, and completion photos.",
            key=f"{key_prefix}_evidence_confirmed",
        )
        submitted = st.form_submit_button(
            "Save Verification Decision",
            type="primary",
            width="stretch",
        )

    if not submitted:
        return
    if not evidence_confirmed:
        st.error("Confirm that the submitted evidence was reviewed.")
        return

    verifier = clean_text(verified_by)
    if verifier and verifier.casefold() == submitted_by.casefold():
        st.warning(
            "The verifier is the same person who submitted the resolution. "
            "Independent verification is recommended where possible."
        )

    approve = decision == "Approve and Close"
    try:
        verify_issue_resolution(
            issue_csv_file,
            issue_id=issue_id,
            verified_by=verified_by,
            verification_notes=verification_notes,
            approve=approve,
        )
    except Exception as error:
        st.error(f"Failed to save the verification decision: {error}")
        return

    if approve:
        _save_success(
            f"{issue_id} was verified and closed. The unit marker was recalculated from all remaining Issues."
        )
    else:
        _save_success(
            f"{issue_id} was rejected and reopened for additional work."
        )

def _render_actions(
    row: pd.Series,
    issue_csv_file: str | Path,
    *,
    key_prefix: str,
) -> None:
    status = clean_text(row.get("Status")) or "Reported"

    if status == "Reported":
        _render_assignment_form(
            row,
            issue_csv_file,
            key_prefix=key_prefix,
            title="Review and Assign",
        )
        return

    if status == "Assigned":
        _render_start_work_form(
            row,
            issue_csv_file,
            key_prefix=key_prefix,
        )
        with st.expander("Update or change the assignment"):
            _render_assignment_form(
                row,
                issue_csv_file,
                key_prefix=f"{key_prefix}_reassign",
                title="Update Assignment",
            )
        return

    if status == "Reopened":
        st.warning(
            "This Issue was reopened. The existing assignee may continue the work, "
            "or an administrator may assign it to someone else."
        )
        _render_start_work_form(
            row,
            issue_csv_file,
            key_prefix=f"{key_prefix}_restart",
        )
        with st.expander("Review and reassign"):
            _render_assignment_form(
                row,
                issue_csv_file,
                key_prefix=f"{key_prefix}_reassign",
                title="Review and Reassign",
            )
        return

    if status == "In Progress":
        _render_progress_update_form(
            row,
            issue_csv_file,
            key_prefix=key_prefix,
        )
        st.divider()
        _render_resolution_submission_form(
            row,
            issue_csv_file,
            key_prefix=key_prefix,
        )
        return

    if status == "Pending Verification":
        _render_verification_form(
            row,
            issue_csv_file,
            key_prefix=key_prefix,
        )
        return

    if status == "Closed":
        st.success("This Issue is closed. No further action is required.")
        return

    st.warning(f"No action form is configured for status: {status}")


def _render_issue_card(
    row: pd.Series,
    issue_csv_file: str | Path,
    *,
    view_key: str,
    expanded: bool = False,
) -> None:
    issue_id = clean_text(row.get("Issue ID"))
    status = clean_text(row.get("Status")) or "Reported"
    priority = clean_text(row.get("Priority")) or "Not set"
    serial = clean_text(row.get("Serial Number")) or "No serial number"
    issue_types = clean_text(row.get("Issue Type")) or "No issue type"
    reported_at = clean_text(row.get("Reported At")) or "No time"
    key_prefix = f"{view_key}_{_safe_key(issue_id)}"

    title = f"{reported_at} | {serial} | {issue_types} | {status}"
    with st.expander(title, expanded=expanded):
        (
            overview_tab,
            evidence_tab,
            resolution_tab,
            history_tab,
            actions_tab,
        ) = st.tabs(
            [
                "Overview",
                "Evidence",
                "Resolution",
                "Activity History",
                "Actions",
            ]
        )

        with overview_tab:
            left, middle, right = st.columns(3)
            with left:
                st.markdown(f"**Issue ID:** {issue_id or '—'}")
                st.markdown(f"**Status:** {status}")
                st.caption(STATUS_HELP.get(status, ""))
                st.markdown(f"**Priority:** {priority}")
                st.markdown(
                    "**Reported By:** "
                    + (
                        clean_text(row.get("Reported By"))
                        or clean_text(row.get("Technician"))
                        or "—"
                    )
                )
                st.markdown(f"**Reported At:** {reported_at}")

            with middle:
                st.markdown(
                    f"**Serial Number:** {clean_text(row.get('Serial Number')) or '—'}"
                )
                st.markdown(f"**Model:** {clean_text(row.get('Model')) or '—'}")
                st.markdown(
                    f"**Location:** {clean_text(row.get('Location')) or '—'}"
                )
                st.markdown(
                    f"**Postal Code:** {clean_text(row.get('Postal Code')) or '—'}"
                )
                st.markdown(
                    f"**Lift Lobby:** {clean_text(row.get('Lift Lobby')) or '—'}"
                )

            with right:
                st.markdown(
                    f"**Reviewed By:** {clean_text(row.get('Reviewed By')) or '—'}"
                )
                st.markdown(
                    f"**Assigned By:** {clean_text(row.get('Assigned By')) or '—'}"
                )
                st.markdown(
                    "**Current Assignee:** "
                    f"{clean_text(row.get('Current Assignee')) or '—'}"
                )
                st.markdown(
                    f"**Due Date:** {clean_text(row.get('Due Date')) or '—'}"
                )
                st.markdown(
                    f"**Started By:** {clean_text(row.get('Started By')) or '—'}"
                )
                st.markdown(
                    f"**Started At:** {clean_text(row.get('Started At')) or '—'}"
                )

            st.markdown(f"**Issue Type:** {issue_types}")
            st.markdown("**Detailed Description**")
            st.write(clean_text(row.get("Detailed Description")) or "—")

            review_notes = clean_text(row.get("Review Notes"))
            assignment_notes = clean_text(row.get("Assignment Notes"))
            if review_notes or assignment_notes:
                st.markdown("**Review and Assignment Notes**")
                if review_notes:
                    st.write(f"Review: {review_notes}")
                if assignment_notes:
                    st.write(f"Assignment: {assignment_notes}")

            st.markdown("**Copy Issue Information**")
            st.code(build_issue_copy_text(row), language=None, wrap_lines=True)

        with evidence_tab:
            _render_evidence(row, issue_csv_file)

        with resolution_tab:
            _render_resolution_submissions(issue_id, issue_csv_file)

        with history_tab:
            _render_history(issue_id, issue_csv_file)

        with actions_tab:
            _render_actions(
                row,
                issue_csv_file,
                key_prefix=key_prefix,
            )


def render_issues_page(
    issue_csv_file: str | Path = "issue_records.csv",
) -> None:
    _show_action_success()

    try:
        records = load_issue_records(issue_csv_file)
    except Exception as error:
        st.error(f"Failed to load Issue records: {error}")
        return

    open_records = records.loc[
        ~records["Status"].map(is_closed_status)
    ].copy()

    focused_issue_id = clean_text(st.session_state.pop("selected_issue_id", ""))
    if focused_issue_id and not records.empty:
        focus_order = (
            ~records["Issue ID"].astype(str).str.strip().eq(focused_issue_id)
        ).astype(int)
        records = records.assign(_FocusOrder=focus_order).sort_values(
            ["_FocusOrder", "Reported At"],
            ascending=[True, False],
        ).drop(columns=["_FocusOrder"])
        open_records = records.loc[
            ~records["Status"].map(is_closed_status)
        ].copy()

    page_header(
        f"Issues ({len(open_records)})",
        "Assign reported Issues, record work, review submitted resolution evidence and close or reopen each case.",
        eyebrow="ISSUE WORKFLOW · CONTROL",
        chip=f"{len(open_records)} OPEN · {len(records)} TOTAL",
        capabilities=[
            ("Assign and start", "Move a newly reported Issue to the person responsible for follow-up."),
            ("Record resolution", "Capture work performed, test results, notes and supporting photos."),
            ("Verify outcome", "Approve and close the case or reopen it with a clear reason."),
        ],
    )

    open_tab, all_tab = st.tabs(
        [
            f"Open Issues ({len(open_records)})",
            f"All Issues ({len(records)})",
        ]
    )

    with open_tab:
        if open_records.empty:
            st.success("There are no open Issues.")
        else:
            for _, row in open_records.iterrows():
                _render_issue_card(
                    row,
                    issue_csv_file,
                    view_key="open",
                    expanded=(clean_text(row.get("Issue ID")) == focused_issue_id),
                )

    with all_tab:
        if records.empty:
            st.info("No Issue Reports have been submitted yet.")
        else:
            for _, row in records.iterrows():
                _render_issue_card(
                    row,
                    issue_csv_file,
                    view_key="all",
                    expanded=(clean_text(row.get("Issue ID")) == focused_issue_id),
                )


__all__ = ["get_open_issue_count", "render_issues_page"]
