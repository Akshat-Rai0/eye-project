import ForceGraph3D from 'react-force-graph-3d';
import { useEffect, useState, useMemo } from 'react';
import * as THREE from 'three';

baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',

export default function Constellation() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);

  // Persistent loader with CORS
  const textureLoader = useMemo(() => {
    const loader = new THREE.TextureLoader();
    loader.setCrossOrigin('anonymous');
    return loader;
  }, []);

  useEffect(() => {
    fetch(`${API_BASE}/documents/graph`)
      .then(res => res.json())
      .then(data => {
        // Origin node at 0,0,0
        const centerNode = {
          id: 'center-origin',
          x: 0, y: 0, z: 0,
          isCenter: true,
          caption: 'Origin'
        };

        // Every node connects to origin
        const originLinks = data.nodes.map(node => ({
          source: 'center-origin',
          target: node.id,
          isOriginLink: true
        }));

        setGraphData({
          nodes: [centerNode, ...data.nodes],
          links: [...data.links, ...originLinks]
        });
        setLoading(false);
      });
  }, []);

  if (loading) return null;

  return (
    <div className="h-[calc(100vh-5rem)] w-full bg-black relative">
      <div className="absolute top-6 left-6 z-10 bg-white text-black text-[10px] font-black uppercase px-3 py-1.5 tracking-tighter">
        Nodes: {graphData.nodes.length - 1}
      </div>

      {selectedNode && !selectedNode.isCenter && (
        <div className="absolute top-6 right-6 z-20 w-80 bg-black border border-white/20 animate-in fade-in duration-300">
          <button onClick={() => setSelectedNode(null)} className="absolute top-2 right-2 z-10 text-white/40 hover:text-white p-2">✕</button>
          <div className="p-4">
            <div className="aspect-square bg-white shadow-2xl mb-4 border-2 border-white overflow-hidden group/preview">
              <img
                src={selectedNode.img}
                alt="Node"
                className="w-full h-full object-contain grayscale group-hover/preview:grayscale-0 transition-all duration-500 cursor-crosshair"
              />
            </div>
            <p className="text-white text-[11px] font-bold uppercase tracking-tight leading-relaxed mb-4 italic">
              "{selectedNode.caption}"
            </p>
            <div className="flex flex-wrap gap-1 mb-6">
              {selectedNode.tags?.map((tag, i) => (
                <span key={i} className="text-[9px] px-1.5 py-0.5 bg-white text-black font-black uppercase">
                  {tag}
                </span>
              ))}
            </div>

            <button
              onClick={() => setSelectedNode(null)}
              className="w-full py-2 bg-white text-black text-[10px] font-black uppercase tracking-widest hover:invert transition-all"
            >
              HIDE PREVIEW
            </button>
          </div>
        </div>
      )}

      <ForceGraph3D
        graphData={graphData}
        backgroundColor="#000000"
        nodeThreeObject={node => {
          if (node.isCenter) {
            // Neon Yellow Origin
            const geom = new THREE.SphereGeometry(3, 16, 16);
            const mat = new THREE.MeshBasicMaterial({ color: 0xFFFF00 });
            return new THREE.Mesh(geom, mat);
          }

          const group = new THREE.Group();

          // Image texture - grayscale in 3D
          const texture = textureLoader.load(node.img, (tex) => {
            tex.colorSpace = THREE.SRGBColorSpace;
            tex.needsUpdate = true;
          });

          const material = new THREE.SpriteMaterial({
            map: texture,
            transparent: true,
            opacity: 0.9
          });
          const sprite = new THREE.Sprite(material);
          sprite.scale.set(24, 24, 1);
          group.add(sprite);

          // White selection ring
          const ring = new THREE.Mesh(
            new THREE.RingGeometry(13.5, 14, 32),
            new THREE.MeshBasicMaterial({
              color: selectedNode?.id === node.id ? 0xffffff : 0xffffff,
              transparent: true,
              opacity: selectedNode?.id === node.id ? 0.8 : 0.1,
              side: THREE.DoubleSide
            })
          );
          group.add(ring);

          return group;
        }}
        // NEON YELLOW LINKS
        linkColor={() => '#FFFF00'}
        linkWidth={link => link.isOriginLink ? 0.8 : 1.2}
        linkDirectionalParticles={1}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleSpeed={0.002}
        onNodeClick={node => setSelectedNode(node)}

        // Physics Tweaks for better spacing
        d3VelocityDecay={0.4}
        d3AlphaDecay={0.01}
        cooldownTicks={100}

        // Custom Forces to reduce clustering
        d3Force={(forceName, force) => {
          if (forceName === 'charge') {
            // Stronger repulsion to separate nodes
            force.strength(-300).distanceMax(500);
          }
          if (forceName === 'link') {
            // Longer links for better spacing, especially from origin
            force.distance(link => link.isOriginLink ? 150 : 50);
          }
          if (forceName === 'center') {
            // Gentle center force
            force.strength(0.05);
          }
        }}
      />
    </div>
  );
}