"""Auto-converted from TypeScript.
Original file: crew-member-task/helper/crew-member-task-message.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
export const CrewMemberTaskMessage = {
  ASSIGNMENT_SUCCESS: 'Crew member assigned to task successfully',
  GPS_COORDINATES_MISSING: 'GPS coordinates not available for this image',
  CREW_MEMBERS_RETRIEVED_SUCCESS: 'Crew members retrieved successfully',
  CREW_MEMBER_HAS_ONGOING_TASK: 'Crew member has an ongoing task',
  SUBSCRIBER_TASK_NOT_FOUND: 'Subscriber flight task not found',
  INCIDENT_FOR_TASK_NOT_FOUND: 'Incident for the specified task not found',
  TASK_HISTORY_RETRIEVED_SUCCESS: 'Task history retrieved successfully',
  ALL_TASKS_RETRIEVED_SUCCESS: 'All tasks retrieved successfully',
  TASK_ACCEPTED_SUCCESS: 'Task accepted successfully',
  TASK_NOT_FOUND: 'Task not found',
  UNAUTHORIZED_TASK_ACCESS: 'You do not have permission to access this task',
  TASK_CANNOT_BE_ACCEPTED:
    'Only new tasks (Crew Member Assigned) can be accepted',
  TASK_CANNOT_BE_BEGUN: 'Only accepted tasks can be begun',
  TASK_DETAILS_RETRIEVED_SUCCESS: 'Task details retrieved successfully',
  TASK_BEGUN_SUCCESS: 'Task begun successfully',
  TASK_CANNOT_BE_REJECTED:
    'Only new tasks (Crew Member Assigned) can be rejected. Once accepted or in progress, rejection is not allowed',
  TASK_REJECTED_SUCCESS: 'Task rejected successfully',
  TASK_CANNOT_BE_STOPPED: 'Only ongoing tasks can be stopped',
  TASK_STOPPED_SUCCESS: 'Task stopped successfully',
  TASK_CANNOT_BE_COMPLETED: 'Only ongoing tasks can be completed',
  COMPLETION_EVIDENCE_REQUIRED:
    'At least one evidence file is required to complete the task',
  TASK_COMPLETED_SUCCESS: 'Task completed successfully',
  TASK_NOT_FOUND_OR_NOT_ASSIGNED:
    'Task not found or crew member not assigned to this task',
};

'''
