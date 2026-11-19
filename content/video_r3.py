"""Round 3 (user review r2, 2026-11-19): 11 frames failed again; rewrites follow the r2 notes. Same fields as video_r2.R."""
R = {
 'aurora_v2': dict(
   front='inside a majestic glacier ice cave with towering walls of translucent glowing sapphire blue ice, smooth wave-like ice ripples on the walls and ceiling, a vast cathedral-like chamber, a distant opening glowing with green aurora light, a frozen turquoise stream on the floor, sparkling ice crystals in the air',
   motion='light shimmers and ripples through the blue ice, the aurora glow pulses through the opening, water drips from icicles and trickles along the frozen stream, fine ice crystals drift and sparkle',
   around='glowing blue ice walls all around, polished ice floor below, a high blue ice ceiling with icicles above', ko='빙하 동굴'),
 'crystal_cave_v2': dict(
   front='inside a real natural cave whose rough rock walls, floor and arched ceiling are lined with thousands of deep purple amethyst crystals, a narrow cave passage leading into darkness, a small underground pool reflecting the purple crystals, a lantern on a rock giving warm light, stalactites hanging from the ceiling',
   motion='the lantern flame flickers and the light dances across the crystal facets, water drips from the stalactites into the pool making ripples, sparkling dust floats',
   around='rough cave walls with amethyst crystals all around, rocky cave floor below, an arched rocky ceiling with stalactites above', ko='자수정 동굴'),
 'fireflies_v1': dict(
   front='a calm summer forest glade at dusk with clearly visible tall trees, ferns and a mossy path, about twenty large glowing fireflies floating close to the viewer between one and four meters away, a deer standing on the path a few meters ahead',
   motion='the nearby fireflies drift slowly and blink softly, the deer lifts its head and walks slowly along the path, ferns and leaves sway in a light breeze',
   around='forest all around, a mossy path and ferns below, a deep blue evening sky through the canopy above'),
 'jurassic_beach_v2': dict(
   front='a primeval cambrian-like shallow seashore with clear tide pools, several large trilobites crawling on the wet sand and rocks in the foreground, horseshoe-crab-like creatures, colorful algae and stromatolites, gentle waves, a volcanic island on the horizon',
   motion='the trilobites crawl slowly with moving legs, waves wash in and out of the tide pools, algae sways in the water, clouds drift over the volcano',
   around='primeval coast all around, wet sand and tide pools below, a hazy prehistoric sky above', ko='원시 해안 2'),
 'moon_surface_v2': dict(
   front='on the lunar surface, two astronauts riding an open lunar rover cart across the grey cratered plain in the middle distance, tire tracks behind them, the blue earth large in the black sky',
   motion='the rover drives slowly over the bumpy surface kicking up fine dust that falls in low gravity, the astronauts sway with the motion and one points ahead, the earth slowly turns',
   around='grey lunar plains and crater rims all around, regolith with tire tracks below, black sky with stars above', ko='달 탐사'),
 'oasis_v2': dict(
   front='close to a desert oasis at dusk, palm trees and a clear pool a few meters away, three camels walking close past the viewer with a rider in desert robes, a small campfire in the foreground',
   motion='the camels walk slowly past the viewer with a natural swaying gait, the rider sways, the palms sway, the campfire flickers, the pool ripples',
   around='dunes all around, sand below, a purple and orange sky above'),
 'solar_system_v2': dict(
   front='a clear view of an imaginary solar system modeled on ours: two suns, a large yellow sun and a smaller blue-white sun, with planets lined up along their orbits in front of them, a red ringed gas giant, a blue ocean planet with a moon, a rocky desert planet, faint thin orbit lines, the black starry space',
   motion='the planets move slowly along their orbits and rotate, the two suns glow and flare softly, a moon circles the ocean planet',
   around='planets and stars all around, black space above and below', ko='쌍둥이 태양계'),
 'sunken_ship_v1': dict(
   front='completely underwater on the sea floor, a large sunken wooden sailing ship covered in coral lying on the sand, deep blue water all around with light rays from the far surface above, a large green sea turtle swimming very close to the viewer in the foreground, big fish around the hull',
   motion='the turtle paddles slowly right in front of the viewer and glides past, the fish swim around the hull, sea fans sway, particles drift in the light rays',
   around='blue water and sea floor all around, sand below, the distant bright surface above'),
 'sunken_ship_v2': dict(
   front='underwater ancient ruins with marble columns covered in seaweed, three large reef sharks spread apart: one swimming close on the left, one in the middle distance between the columns, one passing on the right',
   motion='the sharks glide slowly in different directions with natural tail movements, seaweed sways, light flickers on the stones',
   around='ruins and blue water all around, sand below, soft light above'),
 'sunset_meadow_v2': dict(
   front='close-up savanna at sunset, two tall giraffes standing beside an acacia tree only about ten meters from the viewer, zebras grazing nearby, a cheetah running across the grass in the middle distance',
   motion='the giraffes stretch their necks and pull leaves from the acacia, the zebras graze and swish their tails, the cheetah sprints smoothly across the grass, the grass ripples',
   around='grassland and acacias all around, grass below, a fiery sunset sky above', ko='노을 사바나 2'),
 'whale_ocean_v2': dict(
   front='underwater in the clear blue ocean, a small pod of five dolphins swimming toward the viewer at close range, sun rays from the surface above, a few bubbles',
   motion='the dolphins swim gracefully with natural tail strokes, two of them glide past close to the viewer, light rays dance, bubbles rise',
   around='endless blue water all around, deep blue below, the rippling surface above', ko='돌고래 무리'),
}
assert len(R) == 11
