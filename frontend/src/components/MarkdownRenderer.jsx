import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

/**
 * 图片组件：加载失败时降级为可点击链接，避免出现裂图
 */
function SafeImage({ src, alt }) {
  const [failed, setFailed] = useState(false);

  if (failed) {
    return (
      <a
        href={src}
        target="_blank"
        rel="noreferrer"
        className="inline-block max-w-full break-all text-sm text-blue-600 hover:underline"
      >
        {alt || src}
      </a>
    );
  }

  return (
    <img
      src={src}
      alt={alt || ''}
      className="my-2 max-w-full rounded-lg border border-[#E5E5E5]"
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}

/**
 * Markdown 渲染组件
 * 用于把大模型输出的 Markdown（含图片、表格、代码等）渲染成富文本
 */
const MarkdownRenderer = ({ content }) => {
  if (!content) {
    return null;
  }

  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkBreaks, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          img: SafeImage,
          a: ({ href, children, ...props }) => {
            const isInternal = href && (href.startsWith('/') || href.startsWith('#'));
            if (isInternal) {
              return (
                <Link to={href} className="text-blue-600 hover:underline" {...props}>
                  {children}
                </Link>
              );
            }
            return (
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 hover:underline"
                {...props}
              >
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
