"""Round 4 (user review r3, 2026-11-19): 4 scenes failed again; 7 chosen from A/B (see jobs/first_frame_selection.json)."""
R = {
 'aurora_v2': dict(
   front='inside a beautiful glacier ice cave with smooth flowing walls of luminous clear turquoise and sapphire blue ice, the cave opens naturally at the far end into a wide arched mouth with a view of snowy mountains under a green aurora night sky, soft blue light glowing through the ice, a frozen stream along the floor',
   motion='light glows and ripples softly through the blue ice, the aurora waves gently outside the cave mouth, meltwater trickles along the stream, a few snowflakes drift in through the opening',
   around='glowing blue ice walls all around, polished ice floor below, a smooth blue ice ceiling above', ko='빙하 동굴'),
 'crystal_cave_v2': dict(
   front='inside a natural rock cave whose high arched ceiling is completely covered with clusters of large deep purple amethyst crystals hanging overhead, a smooth dark rocky floor with a still pool reflecting the purple ceiling, a lantern on a rock, the cave passage continuing ahead',
   motion='the lantern flame flickers and the light glints across the amethyst ceiling, water drips from the crystals into the pool making slow ripples, sparkling dust floats',
   around='rocky cave walls all around, a dark rocky floor below, a ceiling covered in purple amethyst crystals above', ko='자수정 동굴'),
 'jurassic_beach_v2': dict(
   front='a beautiful prehistoric beach at golden hour with gentle turquoise waves, a mother long-necked dinosaur and her baby walking slowly in the shallow surf, two plesiosaurs raising their heads out of the calm sea, large spiral ammonite shells on the sand, tree ferns along the shore',
   motion='the mother and baby dinosaur walk slowly through the shallow water with natural steps, the plesiosaurs glide and dip their necks, gentle waves roll onto the sand, fern fronds sway in the sea breeze',
   around='prehistoric coast and ferns all around, golden sand below, a warm golden sky above', ko='원시 해안 2'),
 'whale_ocean_v2': dict(
   front='underwater in the clear blue ocean, a small pod of five dolphins swimming sideways across the view from left to right at medium distance, seen in profile, sun rays from the surface above',
   motion='the dolphins swim sideways across the view from left to right with natural tail strokes, one rises slightly toward the surface, light rays dance, a few bubbles trail',
   around='endless blue water all around, deep blue below, the rippling surface above', ko='돌고래 무리'),
}
assert len(R) == 4
