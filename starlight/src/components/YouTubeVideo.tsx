import React, { useState } from 'react';

interface YouTubeVideoProps {
  /**
   * @schemaDescription External URL for the embedded or linked resource.
   * @ukrainianText false
   */
  url?: string;
  /**
   * @schemaDescription External media identifier.
   * @ukrainianText false
   */
  id?: string;
  /**
   * @schemaDescription Short label for a UI or source item.
   * @ukrainianText true
   */
  label?: string;
}

function extractVideoId(url: string): string | null {
  const match = url.match(/(?:v=|\/embed\/|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  return match ? match[1] : null;
}

export default function YouTubeVideo({ url, id, label }: YouTubeVideoProps) {
  const [playing, setPlaying] = useState(false);
  const videoId = id || (url ? extractVideoId(url) : null);

  if (!videoId) {
    return (
      <a href={url} target="_blank" rel="noopener noreferrer">
        {label || url}
      </a>
    );
  }

  return (
    <div style={{ maxWidth: '480px', margin: '1rem 0' }}>
      {playing ? (
        <div
          style={{
            position: 'relative',
            paddingBottom: '56.25%',
            height: 0,
            overflow: 'hidden',
            borderRadius: '8px',
          }}
        >
          <iframe
            src={`https://www.youtube.com/embed/${videoId}?rel=0`}
            title={label || 'Video'}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              border: 'none',
            }}
          />
        </div>
      ) : (
        <button
          onClick={() => setPlaying(true)}
          aria-label={label ? `Play: ${label}` : 'Play video'}
          style={{
            display: 'block',
            width: '100%',
            position: 'relative',
            padding: 0,
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            borderRadius: '8px',
            overflow: 'hidden',
          }}
        >
          <img
            src={`https://img.youtube.com/vi/${videoId}/hqdefault.jpg`}
            alt={label || 'Video thumbnail'}
            loading="lazy"
            style={{ width: '100%', display: 'block', borderRadius: '8px' }}
          />
          <span
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontSize: '2rem',
              color: '#fff',
              background: 'rgba(255, 0, 0, 0.8)',
              width: '64px',
              height: '44px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '12px',
            }}
          >
            ▶
          </span>
        </button>
      )}
    </div>
  );
}
