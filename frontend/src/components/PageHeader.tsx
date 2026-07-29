type PageHeaderProps = {
  eyebrow: string
  title: string
  description: string
  className?: string
}

export function PageHeader({ eyebrow, title, description, className = '' }: PageHeaderProps) {
  return (
    <section className={`animate-fade-up mb-8 ${className}`}>
      <p className="section-eyebrow mb-3">{eyebrow}</p>
      <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">{title}</h2>
      <p className="animate-fade-up animate-delay-1 mt-3 max-w-3xl text-base leading-relaxed text-slate-400">
        {description}
      </p>
    </section>
  )
}
