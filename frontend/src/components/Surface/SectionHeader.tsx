import type { ReactNode } from 'react';

interface SectionHeaderProps {
  eyebrow: string;
  title: string;
  description?: string;
  meta?: ReactNode;
  action?: ReactNode;
}

export default function SectionHeader({ eyebrow, title, description, meta, action }: SectionHeaderProps) {
  return (
    <div className="surface-header">
      <div className="surface-intro">
        <div className="surface-eyebrow">{eyebrow}</div>
        <h2 className="surface-title">{title}</h2>
        {description ? <p className="surface-description">{description}</p> : null}
      </div>
      {meta || action ? (
        <div className="surface-side">
          {meta ? <div className="surface-meta">{meta}</div> : null}
          {action ? <div className="surface-actions">{action}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
