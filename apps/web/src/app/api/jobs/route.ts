import { NextRequest, NextResponse } from "next/server";

// D-008: this route will enqueue a BullMQ FlowProducer job (one parent per
// book, one child per chapter). Each child job's Node processor calls the
// FastAPI worker service (D-007, services/worker) per chapter. Not wired up
// yet — BullMQ/Redis aren't in the dependency tree, and services/worker's
// pipeline execution is still a stub pending the Phase 0 spike gate.
export async function POST(_req: NextRequest) {
  return NextResponse.json(
    { error: "not_implemented" },
    { status: 501 },
  );
}
