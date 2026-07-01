import { NextRequest } from "next/server";

// D-008: progressive per-chapter delivery via SSE. Once the jobs/chapters
// tables exist, this route should poll for row changes and push
// `{ type: "chapter_done", chapter, audio_url, guide }` events as each
// chapter completes. Stubbed until the DB layer and BullMQ dispatch exist.
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;

  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      controller.enqueue(
        encoder.encode(
          `event: error\ndata: ${JSON.stringify({ job_id: id, error: "not_implemented" })}\n\n`,
        ),
      );
      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
