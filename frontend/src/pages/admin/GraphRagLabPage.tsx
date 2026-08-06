import { PageHeader } from '@/components/PageHeader'
import { GraphRagCompareSection } from '@/components/admin/GraphRagCompareSection'

export function GraphRagLabPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Graph RAG Lab"
        title="Traditional RAG vs Graph RAG"
        description="Compare hybrid search + LLM answers side by side: code chunks only (traditional RAG) versus the same chunks plus knowledge-graph nodes and import edges in the prompt (Graph RAG). Retrieved sources are identical — expand graph context to see what relationships were injected."
        className="mb-6"
      />
      <GraphRagCompareSection />
    </div>
  )
}
