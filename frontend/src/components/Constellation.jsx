import ForceGraph2D from 'react-force-graph-2d';
import { useRef, useEffect, useState } from 'react';

export default function Constellation() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });

  useEffect(() => {
    fetch('http://localhost:8000/api/documents/graph')
      .then(res => res.json())
      .then(setGraphData);
  }, []);

  return (
    <div className="h-screen w-full bg-[#05070a]">
      <ForceGraph2D
        graphData={graphData}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const size = 15 / globalScale;
          const img = new Image();
          img.src = node.img;

          // Draw Image Circle
          ctx.save();
          ctx.beginPath();
          ctx.arc(node.x, node.y, size/2, 0, 2 * Math.PI, false);
          ctx.clip();
          try { ctx.drawImage(img, node.x - size/2, node.y - size/2, size, size); } catch(e) {}
          ctx.restore();

          // Add Glow Border
          ctx.strokeStyle = '#6366f1';
          ctx.lineWidth = 1 / globalScale;
          ctx.stroke();
        }}
        linkColor={() => '#1e293b'}
        linkWidth={0.5}
      />
    </div>
  );
}