/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";

export type HoldGroupIconProps = React.ComponentPropsWithoutRef<"svg"> & {
  percentage?: number;
};

export function HoldGroupIcon({ width = "20", height = "20", className, color = "#8B5CF6" }: HoldGroupIconProps) {
  return (
    <svg width={width} height={height} viewBox="0 0 16 16" className={className} fill="none">
      <circle cx="8" cy="8" r="6" stroke={color} strokeWidth="1.5" />
      <path d="M6.5 5.5v5M9.5 5.5v5" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
