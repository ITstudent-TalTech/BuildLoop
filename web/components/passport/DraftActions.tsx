import Link from "next/link";
import RegenerateDraftButton from "./RegenerateDraftButton";

interface DraftActionsProps {
  projectId: string;
  draftId: string;
}

export default function DraftActions({ projectId, draftId }: DraftActionsProps) {
  return (
    <div className="mt-6 flex items-center justify-end gap-3">
      <RegenerateDraftButton projectId={projectId} />
      <Link
        className="inline-flex items-center rounded-md bg-forest px-6 py-3 font-medium text-white transition hover:bg-forest/95"
        href={`/passport/${projectId}/review`}
      >
        Review and edit →
      </Link>
      <span className="sr-only">Draft id {draftId}</span>
    </div>
  );
}
