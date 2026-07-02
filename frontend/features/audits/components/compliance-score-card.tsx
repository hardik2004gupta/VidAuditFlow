"use client";

import { animate, useMotionValue, useMotionValueEvent, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";
import { RadialBar, RadialBarChart, PolarAngleAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskBadge } from "@/features/audits/components/risk-badge";
import type { RiskLevel } from "@/types/api";

const RISK_COLOR_VAR: Record<RiskLevel, string> = {
  LOW: "var(--success)",
  MEDIUM: "var(--warning)",
  HIGH: "var(--critical)",
};

interface ComplianceScoreCardProps {
  score: number;
  riskLevel: RiskLevel;
}

/**
 * The compliance-score gauge -- one of UI_VISION.md's four designated
 * "signature wow moments": the score counts up from 0 (via a Framer Motion
 * spring driving the displayed number) in sync with Recharts' own radial
 * arc sweep animation, instead of rendering static.
 */
export function ComplianceScoreCard({ score, riskLevel }: ComplianceScoreCardProps) {
  const shouldReduceMotion = useReducedMotion();
  const motionScore = useMotionValue(0);
  const [displayScore, setDisplayScore] = useState(shouldReduceMotion ? score : 0);

  useMotionValueEvent(motionScore, "change", (latest) => setDisplayScore(Math.round(latest)));

  useEffect(() => {
    if (shouldReduceMotion) {
      setDisplayScore(score);
      return;
    }
    const controls = animate(motionScore, score, { duration: 1.1, ease: "easeOut" });
    return () => controls.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [score, shouldReduceMotion]);

  const data = [{ value: score, fill: RISK_COLOR_VAR[riskLevel] }];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Compliance Score</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4 pb-6">
        <div className="relative h-40 w-40">
          <RadialBarChart
            width={160}
            height={160}
            innerRadius="72%"
            outerRadius="100%"
            barSize={11}
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} axisLine={false} />
            <RadialBar
              background={{ fill: "var(--muted)" }}
              dataKey="value"
              cornerRadius={20}
              isAnimationActive={!shouldReduceMotion}
              animationDuration={1100}
            />
          </RadialBarChart>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-technical text-4xl font-semibold tabular-nums text-foreground">
              {displayScore}
            </span>
            <span className="text-xs text-muted-foreground">out of 100</span>
          </div>
        </div>
        <RiskBadge level={riskLevel} />
      </CardContent>
    </Card>
  );
}
