import React from 'react';

export function Skeleton({ className = '', count = 1, width, height, circle = false }) {
  const items = Array.from({ length: count }, (_, i) => (
    <div
      key={i}
      className={`animate-pulse bg-gray-200 dark:bg-gray-700 rounded ${circle ? 'rounded-full' : ''} ${className}`}
      style={{ width, height }}
    />
  ));
  return count === 1 ? items[0] : <div className="space-y-2">{items}</div>;
}

export function SkeletonCard({ className = '' }) {
  return (
    <div className={`card p-5 space-y-4 ${className}`}>
      <div className="flex items-center gap-4">
        <Skeleton width={40} height={40} circle />
        <div className="flex-1 space-y-2">
          <Skeleton width="60%" height={20} />
          <Skeleton width="40%" height={14} />
        </div>
      </div>
      <Skeleton width="100%" height={60} />
      <div className="flex gap-2">
        <Skeleton width={80} height={28} />
        <Skeleton width={80} height={28} />
      </div>
    </div>
  );
}

export function SkeletonTable({ rows = 5, columns = 4 }) {
  return (
    <div className="card overflow-hidden">
      <div className="bg-gray-50 dark:bg-gray-800 px-4 py-3 flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} width={`${100 / columns}%`} height={16} />
        ))}
      </div>
      <div className="divide-y divide-gray-100 dark:divide-gray-800">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="px-4 py-4 flex gap-4">
            {Array.from({ length: columns }).map((_, j) => (
              <Skeleton key={j} width={`${100 / columns}%`} height={16} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function SkeletonStats({ count = 4 }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card p-6 space-y-3">
          <div className="flex items-center justify-between">
            <Skeleton width={100} height={14} />
            <Skeleton width={40} height={40} circle />
          </div>
          <Skeleton width="50%" height={32} />
        </div>
      ))}
    </div>
  );
}

export function SkeletonChat() {
  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <Skeleton width={32} height={32} circle />
        <div className="flex-1 max-w-[80%] space-y-2">
          <Skeleton width="100%" height={60} />
        </div>
      </div>
      <div className="flex gap-3 justify-end">
        <div className="flex-1 max-w-[80%] space-y-2">
          <Skeleton width="100%" height={40} />
        </div>
        <Skeleton width={32} height={32} circle />
      </div>
      <div className="flex gap-3">
        <Skeleton width={32} height={32} circle />
        <div className="flex-1 max-w-[80%] space-y-2">
          <Skeleton width="100%" height={80} />
        </div>
      </div>
    </div>
  );
}

