/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { describe, expect, it } from "vitest";
import type { IState, IStateResponse, TIssue } from "@plane/types";
import { getDistributionPathsPostUpdate } from "../distribution-update";
import { orderStateGroups, sortStates } from "./state";

const createState = (id: string, group: IState["group"], sequence = 1): IState => ({
  id,
  color: "#000000",
  default: false,
  description: "",
  group,
  name: id,
  project_id: "project-id",
  sequence,
  workspace_id: "workspace-id",
  order: sequence,
});

const issue: TIssue = {
  id: "issue-id",
  sequence_id: 1,
  name: "Issue",
  sort_order: 1,
  state_id: "hold-state",
  priority: null,
  label_ids: [],
  assignee_ids: [],
  estimate_point: "estimate-id",
  sub_issues_count: 0,
  attachment_count: 0,
  link_count: 0,
  project_id: "project-id",
  parent_id: null,
  cycle_id: null,
  module_ids: null,
  type_id: null,
  created_at: "",
  updated_at: "",
  start_date: null,
  target_date: null,
  completed_at: null,
  archived_at: null,
  created_by: "user-id",
  updated_by: "user-id",
  is_draft: false,
};

describe("work-item states", () => {
  it("orders all six state groups canonically", () => {
    const groups: IStateResponse = { started: [], hold: [], backlog: [] };

    expect(Object.keys(orderStateGroups(groups) ?? {})).toEqual([
      "backlog",
      "unstarted",
      "hold",
      "started",
      "completed",
      "cancelled",
    ]);
  });

  it("sorts Hold before Started even when states arrive in reverse order", () => {
    const states = [createState("started", "started"), createState("hold", "hold")];

    expect(sortStates(states)?.map((state) => state.group)).toEqual(["hold", "started"]);
  });

  it("maps Hold issue and estimate updates to the existing Started distribution", () => {
    const { pathUpdates } = getDistributionPathsPostUpdate(
      undefined,
      issue,
      {
        "hold-state": createState("hold-state", "hold"),
      },
      () => ({
        id: "estimate-id",
        key: 1,
        value: "3",
        description: undefined,
        workspace: undefined,
        project: undefined,
        estimate: undefined,
        created_at: undefined,
        updated_at: undefined,
        created_by: undefined,
        updated_by: undefined,
      })
    );

    expect(pathUpdates).toEqual(
      expect.arrayContaining([
        { path: ["started_issues"], value: 1 },
        { path: ["started_estimate_points"], value: 3 },
      ])
    );
    expect(pathUpdates.some(({ path }) => path[0] === "hold_issues")).toBe(false);
  });
});
