/**
 * Trend with no axes: the shape carries the meaning, the labels sit beside it.
 * Values are normalised to their own min/max so a 4-point move is still visible.
 */
export default function Sparkline({
  values,
  width = 132,
  height = 36,
  label,
  className,
}: {
  values: number[];
  width?: number;
  height?: number;
  label?: string;
  className?: string;
}) {
  if (values.length < 2) return null;

  const pad = 3;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const stepX = (width - pad * 2) / (values.length - 1);

  const points = values.map((v, i) => {
    const x = pad + i * stepX;
    const y = height - pad - ((v - min) / span) * (height - pad * 2);
    return [x, y] as const;
  });

  const line = points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${pad},${height - pad} ${line} ${width - pad},${height - pad}`;
  const [lastX, lastY] = points[points.length - 1];

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      role="img"
      aria-label={label ?? `Trend across ${values.length} points`}
    >
      <polygon points={area} fill="var(--brand)" opacity={0.12} />
      <polyline
        points={line}
        fill="none"
        stroke="var(--brand-strong)"
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={lastX} cy={lastY} r={2.5} fill="var(--brand-strong)" />
    </svg>
  );
}
