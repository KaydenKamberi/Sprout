import { STEM_D, LEAF_TRANSFORMS, TENDRIL_PATHS } from "./vineData";

// Leaf index nearest each menu item's centre: the mockup's items are 64px tall,
// starting 26px down, and the vine's leaves sit at fixed heights along the stem.
const ITEM_LEAVES = [1, 3, 5, 8, 10, 12];

export default function Vine({ activeItem }: { activeItem: number }) {
  const currentLeaf = activeItem >= 0 ? ITEM_LEAVES[activeItem] : -1;
  return (
    <svg className="vine" viewBox="0 0 110 712" preserveAspectRatio="none" aria-hidden="true">
      <path className="stem" d={STEM_D} />
      {TENDRIL_PATHS.map((tendril) => (
        <path
          key={tendril.transform + tendril.d}
          className="tendril"
          transform={tendril.transform}
          d={tendril.d}
        />
      ))}
      {LEAF_TRANSFORMS.map((transform, index) => (
        <g
          key={transform}
          transform={transform}
          className={index === currentLeaf ? "leaf current" : "leaf"}
        >
          <path className="blade" d="M0,0 C8,-11 24,-13 35,-2 C24,9 8,9 0,0 Z" />
          <path className="vein" d="M2,-0.5 C12,-3 23,-4 32,-2.5" />
        </g>
      ))}
    </svg>
  );
}
