import { SectionHeader } from "@/components/shared/section-header";

const STACK = [
  { group: "AI Pipeline", items: ["LangGraph", "LangChain", "OpenAI", "FAISS"] },
  { group: "Backend", items: ["FastAPI", "SQLModel", "Alembic", "PostgreSQL"] },
  { group: "Frontend", items: ["Next.js 15", "TypeScript", "TailwindCSS", "shadcn/ui"] },
  { group: "Infra", items: ["Vercel", "Render", "Supabase"] },
] as const;

export function TechStackSection() {
  return (
    <section id="stack" className="content-container py-16 sm:py-24">
      <SectionHeader
        title="Built on a modern, boring-on-purpose stack"
        description="No Kubernetes, no microservices -- a small set of managed services chosen for reliability."
      />
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {STACK.map((group) => (
          <div key={group.group} className="rounded-lg border border-border bg-card p-5">
            <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              {group.group}
            </h3>
            <ul className="mt-3 space-y-2">
              {group.items.map((item) => (
                <li key={item} className="font-technical text-sm text-foreground">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
