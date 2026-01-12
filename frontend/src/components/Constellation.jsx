import ForceGraph2D from 'react-force-graph-2d';
import { useEffect, useState } from 'react';

export default function Constellation() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [imageCache, setImageCache] = useState({});

  useEffect(() => {
    fetch('http://localhost:8000/documents/graph')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch graph data');
        return res.json();
      })
      .then(data => {
        console.log('Graph data:', data);
        setGraphData(data);
        setLoading(false);
        
        // Preload images
        const cache = {};
        data.nodes.forEach(node => {
          const img = new Image();
          img.src = node.img;
          img.onload = () => {
            cache[node.id] = img;
            setImageCache(prev => ({ ...prev, [node.id]: img }));
          };
        });
      })
      .catch(err => {
        console.error('Error loading graph:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="h-[calc(100vh-5rem)] w-full bg-[#05070a] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4 mx-auto" />
          <p className="text-slate-400">Loading constellation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-[calc(100vh-5rem)] w-full bg-[#05070a] flex items-center justify-center">
        <div className="text-center text-red-400">
          <p>Error loading graph: {error}</p>
          <p className="text-sm text-slate-500 mt-2">Make sure images have been processed with embeddings</p>
        </div>
      </div>
    );
  }

  if (!graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="h-[calc(100vh-5rem)] w-full bg-[#05070a] flex items-center justify-center">
        <div className="text-center text-slate-400">
          <p>No images with embeddings yet</p>
          <p className="text-sm text-slate-500 mt-2">Upload some images and wait for processing</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-5rem)] w-full bg-[#05070a] relative">
      {/* Compact stats overlay */}
      <div className="absolute top-4 left-4 z-10 bg-slate-900/80 backdrop-blur-sm border border-slate-700 rounded-xl px-4 py-2.5 text-sm">
        <div className="text-slate-300 flex items-center gap-4">
          <span className="flex items-center gap-2">
            <span className="text-indigo-400 font-semibold">{graphData.nodes.length}</span> 
            <span className="text-slate-500">images</span>
          </span>
          <span className="text-slate-700">•</span>
          <span className="flex items-center gap-2">
            <span className="text-indigo-400 font-semibold">{graphData.links.length}</span>
            <span className="text-slate-500">connections</span>
          </span>
        </div>
      </div>

      {/* Image Preview Modal */}
      {selectedNode && (
        <div 
          className="absolute top-4 right-4 z-20 bg-slate-900/95 backdrop-blur-md border border-indigo-500/50 rounded-2xl shadow-2xl overflow-hidden"
          style={{ width: '320px' }}
        >
          <div className="relative">
            <button
              onClick={() => setSelectedNode(null)}
              className="absolute top-2 right-2 z-10 p-1.5 bg-slate-950/80 hover:bg-slate-950 rounded-full text-slate-400 hover:text-white transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            
            <div className="aspect-square bg-black flex items-center justify-center">
              <img
                src={selectedNode.img}
                alt="Preview"
                className="w-full h-full object-contain"
              />
            </div>
            
            <div className="p-4">
              <p className="text-white text-sm leading-relaxed mb-3">
                {selectedNode.caption || 'Processing...'}
              </p>
              
              <div className="flex flex-wrap gap-1.5">
                {selectedNode.tags?.slice(0, 6).map((tag, i) => (
                  <span 
                    key={i} 
                    className="text-[10px] px-2 py-1 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <ForceGraph2D
        graphData={graphData}
        width={window.innerWidth}
        height={window.innerHeight - 80}
        nodeCanvasObject={(node, ctx, globalScale) => {
          const size = 70 / Math.max(globalScale, 0.5);
          const cachedImg = imageCache[node.id];
          
          if (!cachedImg) return;
          
          // Outer glow
          ctx.shadowBlur = 15;
          ctx.shadowColor = '#6366f1';
          
          // Calculate crop to show image as a perfect circle (center crop)
          const imgAspect = cachedImg.width / cachedImg.height;
          let sx, sy, sWidth, sHeight;
          
          if (imgAspect > 1) {
            // Wider than tall - crop sides
            sHeight = cachedImg.height;
            sWidth = cachedImg.height;
            sx = (cachedImg.width - sWidth) / 2;
            sy = 0;
          } else {
            // Taller than wide - crop top/bottom
            sWidth = cachedImg.width;
            sHeight = cachedImg.width;
            sx = 0;
            sy = (cachedImg.height - sHeight) / 2;
          }
          
          // Draw circular clipped image
          ctx.save();
          ctx.beginPath();
          ctx.arc(node.x, node.y, size / 2, 0, 2 * Math.PI, false);
          ctx.closePath();
          ctx.clip();
          
          // Draw the cropped image
          ctx.drawImage(
            cachedImg,
            sx, sy, sWidth, sHeight,  // Source rectangle (square crop from center)
            node.x - size / 2, node.y - size / 2, size, size  // Destination
          );
          
          ctx.restore();

          // Glowing border
          ctx.strokeStyle = selectedNode?.id === node.id ? '#818cf8' : '#6366f1';
          ctx.lineWidth = selectedNode?.id === node.id ? 4 / globalScale : 3 / globalScale;
          ctx.shadowBlur = selectedNode?.id === node.id ? 20 : 10;
          ctx.shadowColor = '#6366f1';
          ctx.beginPath();
          ctx.arc(node.x, node.y, size / 2, 0, 2 * Math.PI, false);
          ctx.stroke();
          
          ctx.shadowBlur = 0;
        }}
        nodeLabel={node => {
          const caption = node.caption || 'Processing...';
          const tags = node.tags?.slice(0, 5).join(', ') || 'No tags yet';
          return `
            <div style="
              background: rgba(15, 23, 42, 0.98); 
              padding: 12px; 
              border-radius: 12px; 
              border: 1px solid #4f46e5;
              box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
              max-width: 300px;
            ">
              <div style="
                color: white; 
                font-weight: 600; 
                margin-bottom: 8px;
                font-size: 13px;
                line-height: 1.4;
              ">${caption}</div>
              <div style="
                color: #94a3b8; 
                font-size: 11px;
                padding-top: 8px;
                border-top: 1px solid #334155;
              ">🏷️ ${tags}</div>
            </div>
          `;
        }}
        linkColor={link => 'rgba(99, 102, 241, 0.3)'}
        linkWidth={2}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleSpeed={0.005}
        backgroundColor="#05070a"
        cooldownTicks={100}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        enablePanInteraction={true}
        onNodeClick={node => {
          setSelectedNode(node);
        }}
        onNodeHover={node => {
          document.body.style.cursor = node ? 'pointer' : 'default';
        }}
      />
    </div>
  );
}