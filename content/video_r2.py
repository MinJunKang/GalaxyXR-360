"""Round 2 (user review 2026-11-19): 47 first frames failed; each rewrite follows the reviewer's note.
Entry: name -> dict(front, motion, around[, ko]) ; 'ko' overrides the app title when the concept changed.
front  : the first frame (static, eye-level, 90 deg rectilinear) INCLUDING the large moving subjects, placed close enough to read
motion : natural motion for the 10 s clip — environment (water, leaves, flowers, fire, clouds) AND subjects (animals, vehicles, people)
around : the rest of the sphere for CubeComposer
"""
R = {
 # ---------------- healing ----------------
 'forest_morning_v1': dict(
   front='an ancient misty pine forest at sunrise with golden god rays, a red deer stag with large antlers standing in the clearing about fifteen meters ahead, two water deer grazing behind it, a jay perched on a low branch in the foreground, ferns and moss covered in dew',
   motion='the stag raises its head and walks slowly across the clearing with a natural gait, the water deer graze and flick their ears, the jay hops and flies off to another branch, mist drifts between the trunks, fern fronds and pine needles sway gently, sunbeams shimmer',
   around='pine trunks and mist in every direction, a winding dirt trail behind, moss and ferns below, a pale sunrise sky through the treetops above'),
 'forest_morning_v2': dict(
   front='a clear forest stream winding through a sunlit birch forest in early summer, mossy stones and small cascades, two brown wild rabbits sitting on the grassy bank in the foreground, a kingfisher on a branch over the water, wildflowers along the banks',
   motion='the stream flows and splashes over the stones with sparkling ripples, the rabbits nibble grass and hop a few steps, the kingfisher dives into the water and flies back to its branch, birch leaves and wildflowers sway in the breeze',
   around='birch forest on both banks, the stream continuing behind, grass and stones below, blue sky through the leaves above'),
 'lake_dawn_v2': dict(
   front='a turquoise glacial lake surrounded by dramatic snowy peaks at sunrise, a red wooden canoe with a paddler gliding across the water in the middle distance, a pair of loons swimming near the shore, wisps of golden mist on the surface',
   motion='the paddler strokes rhythmically and the canoe glides across the lake leaving a widening wake, the loons swim and dive, the mist drifts and glows, small waves lap the pebble shore',
   around='snowy peaks and pine forest around the lake, pebbles and water below, a pink and gold sunrise sky above'),
 'flower_field_v1': dict(
   front='a lush english cottage garden in full bloom at golden hour, beds of roses, foxgloves, peonies, lavender and delphiniums in many colors, a gravel path with a stone fountain, a wooden arch covered in climbing roses, several large swallowtail butterflies and a hummingbird among the flowers',
   motion='the flowers and tall stems sway softly in the warm breeze, petals drift down, the butterflies flutter from flower to flower, the hummingbird hovers and darts, water bubbles in the fountain',
   around='flower beds and hedges all around the garden, a gravel path below, a golden evening sky above', ko='꽃 정원 1'),
 'flower_field_v2': dict(
   front='a colorful landscaped flower garden in the countryside with tulips, poppies, cosmos and sunflowers in curved beds, a white horse with a foal walking along the grass path in the middle distance, a few sheep grazing beyond a low stone wall',
   motion='the horse and foal walk slowly along the path with a natural gait and swishing tails, the sheep graze and move a few steps, flowers sway in waves of wind, clouds drift',
   around='flower beds and green hills all around, a grass path below, a blue sky with white clouds above', ko='꽃 정원 2'),
 'autumn_valley_v1': dict(
   front='standing on a leaf-covered forest path inside a blazing autumn maple forest, red and orange maple trees arching overhead, a clear stream beside the path with a small wooden bridge, a red squirrel on a fallen log in the foreground and a deer drinking at the stream',
   motion='red leaves fall and spiral slowly through the air, the stream flows over stones, the squirrel nibbles a nut and scurries along the log, the deer lifts its head and steps back from the water, branches sway gently',
   around='autumn maple forest in every direction, a leaf-covered path below, red canopy and blue sky above'),
 'snow_cabin_v1': dict(
   front='a cozy log cabin in a snowy pine forest at dusk, a crackling campfire with logs and a stone ring in the foreground, warm orange light in the windows, smoke rising from the chimney, a wooden bench with a blanket beside the fire',
   motion='the campfire flames flicker and dance, sparks float upward, smoke curls from the chimney, snow falls softly and steadily in large flakes, the window light glows warmly',
   around='snow-laden pine trees all around, deep snow below, a deep twilight blue sky with falling snow above'),
 'snow_cabin_v2': dict(
   front='a small wooden cabin with glowing windows in a snowy clearing during heavy snowfall at blue hour, a snow-covered pine forest behind, a lantern on the porch, a red fox standing in the snow in the foreground',
   motion='large snowflakes fall steadily, the fox sniffs the snow and trots slowly past the cabin, the lantern flickers, smoke drifts from the chimney, snow slides off a pine branch',
   around='snowy pines around the clearing, deep snow below, a dim blue sky full of falling snow above'),
 'rainy_window_v2': dict(
   front='a dense tropical rainforest during heavy rain, huge leaves and hanging vines glistening with water, a small waterfall into a pool, a pair of toucans on a branch and a capybara at the edge of the pool',
   motion='rain pours down and drips from every leaf, puddles and the pool ripple with raindrops, the waterfall flows, the toucans shake off water and hop along the branch, the capybara walks slowly into the pool',
   around='rainforest in every direction, wet roots and mud below, a dark rainy canopy above'),
 'aurora_v2': dict(
   front='inside a glacier ice cave with translucent blue ice walls, an opening at the far end showing green aurora over the night sky, icicles hanging from the ceiling, a frozen stream on the cave floor',
   motion='the aurora waves and shimmers through the opening, light ripples across the blue ice, water drips from the icicles, fine snow blows in through the entrance',
   around='glowing blue ice walls all around, ice floor below, ice ceiling with icicles above', ko='빙하 동굴'),
 'sunset_meadow_v1': dict(
   front='an african savanna at sunset with a single acacia tree, a family of elephants walking in the middle distance, a lion resting on a rock in the foreground, golden grass',
   motion='the elephants walk slowly with swinging trunks and flapping ears, the lion lifts its head and looks around, the grass sways in the wind, dust glows in the low sun',
   around='open savanna all around, golden grass below, an orange sunset sky above', ko='노을 사바나 1'),
 'sunset_meadow_v2': dict(
   front='rolling golden grassland at sunset with a group of giraffes near acacia trees and a cheetah running across the plain in the middle distance, a herd of zebras behind',
   motion='the cheetah sprints smoothly across the grass, the giraffes walk slowly and stretch their necks to the leaves, the zebras graze and swish their tails, the grass ripples in long waves',
   around='grassland and distant hills all around, grass below, a fiery sunset sky above', ko='노을 사바나 2'),
 'starry_night_v1': dict(
   front='a vast majestic desert valley at night with towering red rock arches, the brilliant milky way arching over the arch, a glowing orange tent on the valley floor, countless stars',
   motion='several shooting stars streak slowly across the sky, the stars twinkle, the tent glows softly, a faint breeze moves the desert grass',
   around='red rock formations around the valley, sand below, the milky way across the whole sky above'),
 'starry_night_v2': dict(
   front='a mountain lake at night under a sky full of stars and a green aurora, a wooden canoe with a lantern drifting on the lake, the stars and aurora reflected in the water',
   motion='the aurora waves slowly across the sky, its reflection ripples, the lantern glows and the canoe drifts gently, a shooting star crosses the sky',
   around='dark mountains around the lake, stones and water below, stars and aurora above'),
 'fireflies_v1': dict(
   front='a summer forest glade at dusk with clearly visible tall trees, ferns and a winding path, a moderate number of glowing fireflies floating between the trees, a deer standing on the path',
   motion='the fireflies drift and blink softly, the deer walks slowly along the path, leaves and ferns sway, the last evening light fades through the trees',
   around='forest all around, a path and ferns below, a deep blue evening sky through the canopy above'),
 # ---------------- ocean / underwater ----------------
 'cliff_coast_v2': dict(
   front='towering white chalk sea cliffs above a turquoise sea at sunset, waves breaking at the foot of the cliffs, a lighthouse on the cliff top, a flock of seagulls and a sailboat on the sea',
   motion='waves roll in and crash against the base of the cliffs with white foam, the seagulls glide and wheel in the wind, the sailboat sails slowly along the coast, clouds drift',
   around='the cliff coastline on both sides, grassy cliff top behind, the sea ahead and below, a golden sky above'),
 'coral_reef_v1': dict(
   front='a vibrant tropical coral reef in clear water, a large green sea turtle swimming close to the viewer in the foreground, schools of colorful fish nearby at medium distance, sun rays from the surface',
   motion='the turtle paddles slowly with its flippers and glides past the viewer, the schools of fish turn together, soft corals sway in the current, light caustics dance',
   around='coral reef in every direction, sand and corals below, the bright rippling surface above'),
 'kelp_forest_v1': dict(
   front='an underwater kelp forest with sunlight beams, a large school of big silver fish swimming close to the viewer, a sea lion gliding between the kelp, orange garibaldi fish near the rocks',
   motion='the kelp sways in the current, the large fish school swirls and changes direction, the sea lion twists and glides past, light beams shimmer',
   around='kelp forest all around, rocks below, the bright surface above'),
 'whale_ocean_v2': dict(
   front='the open blue ocean just below the surface with a pod of dolphins swimming close to the viewer, sun rays from above',
   motion='the dolphins swim and arc gracefully, some rise toward the surface for air, the light rays dance, bubbles trail behind them',
   around='endless blue water all around, deep blue below, the rippling surface above'),
 'jellyfish_v2': dict(
   front='deep blue open ocean with a large sea turtle and two big sharks swimming at medium distance, sun rays from the surface, small fish around',
   motion='the sharks glide slowly with gentle tail beats, the turtle paddles calmly, the small fish scatter and regroup, light rays shimmer',
   around='blue water all around, darker depths below, the surface above', ko='상어와 거북'),
 'sunken_ship_v1': dict(
   front='a large sunken wooden sailing ship on the sea floor covered in coral, big groupers and a school of large fish swimming close in the foreground, a sea turtle beside the hull',
   motion='the large fish swim slowly past the viewer, the turtle glides along the hull, sea fans sway, particles drift in the light rays',
   around='sea floor with scattered barrels around, sand below, blue water and sunlight above'),
 'sunken_ship_v2': dict(
   front='underwater ancient ruins with marble columns covered in seaweed, three large reef sharks swimming between the columns, rays of sunlight',
   motion='the sharks glide slowly between the columns with natural tail movements, seaweed sways, light flickers on the stones',
   around='ruins and blue water all around, sand below, soft light above'),
 'tropical_beach_v2': dict(
   front='scuba diving view in a tropical sea, a colorful coral reef with sea fans and seaweed, countless tropical fish of many colors swimming close around the viewer, a clownfish anemone in the foreground',
   motion='the fish swim and dart around the viewer, the anemone tentacles and seaweed sway in the current, bubbles rise, sunlight flickers',
   around='reef and fish in every direction, corals below, the bright surface above', ko='스쿠버 다이빙'),
 # ---------------- space ----------------
 'mars_v1': dict(
   front='an imaginative alien world inspired by a vast ancient sea basin, a calm turquoise sea with glowing shores, enormous eroded red and white rock towers, two moons in a pastel sky, a flock of large translucent winged creatures gliding',
   motion='waves roll slowly onto the glowing shore, the winged creatures glide and turn, thin clouds drift past the moons, mist rises from the sea',
   around='rock towers and the sea all around, glowing sand below, a pastel sky with two moons above', ko='외계 바다'),
 'mars_v2': dict(
   front='a beautiful dynamic alien planet with giant crystal mountains, rivers of glowing blue water flowing through purple valleys, huge floating jellyfish-like creatures drifting in the sky, a ringed planet on the horizon',
   motion='the glowing rivers flow and sparkle, the floating creatures drift and pulse slowly, clouds move across the ringed planet, crystal spires glint',
   around='alien valleys all around, glowing ground below, a colorful sky above', ko='외계 행성 계곡'),
 'moon_surface_v2': dict(
   front='standing on the lunar surface near a crater rim, a moon base with domes in the middle distance, an astronaut walking toward the base, earth large in the black sky',
   motion='the astronaut walks slowly with a low-gravity gait kicking up dust, a rover drives along the crater rim, the earth slowly turns',
   around='grey lunar plains and crater rims all around, regolith below, black sky with stars above'),
 'saturn_rings_v2': dict(
   front='inside the asteroid belt between mars and jupiter, large tumbling rocky asteroids of many sizes close to the viewer, the distant sun shining, jupiter visible far away',
   motion='the asteroids tumble and drift slowly, sunlight glints on their surfaces, small rocks collide softly and scatter',
   around='asteroids in every direction, black space with stars above and below', ko='소행성 지대'),
 'milky_way_v1': dict(
   front='a breathtaking view of the milky way core with vivid colorful nebulae in pink, gold and blue, dense star clouds and dark dust lanes, a bright comet nearby',
   motion='the comet moves slowly with its glowing tail, the stars twinkle, the nebulae glow softly',
   around='stars and nebulae in every direction, above and below'),
 'solar_system_v2': dict(
   front='an imaginary solar system with two suns, a large orange sun and a small blue-white sun, ringed gas giants and colorful planets in the foreground, an asteroid belt glittering',
   motion='the planets orbit and rotate slowly, the two suns glow and flare softly, asteroids drift',
   around='planets and stars all around, black space above and below', ko='쌍둥이 태양계'),
 'space_station_v2': dict(
   front='floating in space outside a large space station with solar panels, an astronaut on a spacewalk on the station arm, planet earth huge and blue below',
   motion='the station rotates slowly, the astronaut moves along the arm with careful natural motions, clouds drift over the earth, sunlight glints on the panels',
   around='the station structure around, earth below, black space with stars above'),
 # ---------------- sci-fi ----------------
 'cyber_city_v1': dict(
   front='a dense gritty cyberpunk street at night in heavy rain, cluttered neon signs in many languages, holographic billboards, tangled cables, steaming street food stalls, people with glowing umbrellas walking, a flying car passing overhead',
   motion='rain falls, neon signs flicker and buzz, holograms shimmer, people walk naturally under umbrellas, steam rises, the flying car glides past with light trails',
   around='neon buildings on both sides and behind, wet reflective street below, dark rainy sky with flying vehicles above'),
 'crystal_cave_v2': dict(
   front='a giant amethyst geode cave with walls covered in large purple quartz crystals, soft violet light, a still pool reflecting the crystals, a small waterfall trickling down the crystals',
   motion='the waterfall trickles, the pool ripples gently, light glints and shifts across the crystal facets, sparkling dust floats',
   around='purple crystal walls all around, crystal floor below, crystal ceiling above', ko='자수정 동굴'),
 # ---------------- desert ----------------
 'sahara_dunes_v1': dict(
   front='golden sahara dunes at sunset with a camel caravan of five camels and a nomad walking along a dune ridge in the middle distance',
   motion='the camels walk slowly in a line with a natural swaying gait, the nomad leads them, sand blows from the dune crests, long shadows move',
   around='dunes in every direction, rippled sand below, an orange to blue sky above'),
 'oasis_v2': dict(
   front='a desert oasis at dusk with palm trees and a pool, a caravan of camels walking past the oasis with a rider, a small campfire',
   motion='the camels walk slowly past the palms with a natural gait, the palms sway, the campfire flickers, the pool ripples',
   around='dunes all around, sand below, a purple and orange sky above'),
 'canyon_v2': dict(
   front='standing on a ledge inside a wide red rock canyon at sunrise, cliffs rising on both sides, a river flowing at the canyon floor below, a hot air balloon floating between the cliffs, eagles circling',
   motion='the river flows and sparkles, the balloon drifts slowly through the canyon, the eagles circle on the wind, sunlight spreads over the cliffs',
   around='canyon walls on both sides and behind, a rock ledge below, a sunrise sky above'),
 # ---------------- countryside ----------------
 'country_farm_v2': dict(
   front='a traditional korean hanok village with curved tiled roofs and stone walls, persimmon trees with orange fruit, villagers in hanbok walking along a narrow lane, a magpie on a wall',
   motion='the villagers walk slowly along the lane, the magpie hops and flies, persimmon leaves flutter, smoke rises from a chimney',
   around='hanok houses all around, an earthen lane below, a clear autumn sky above', ko='한옥 마을'),
 # ---------------- jurassic ----------------
 'jurassic_jungle_v1': dict(
   front='a prehistoric jurassic jungle beside a wide river, giant tree ferns and conifers, several large pterosaurs flying low over the river, a distant smoking volcano',
   motion='the pterosaurs flap and glide over the river, the river flows, ferns sway, mist drifts',
   around='prehistoric jungle all around, ferns and mud below, a hazy sky above'),
 'jurassic_jungle_v2': dict(
   front='a huge brachiosaurus standing close to the viewer among giant ferns, its long neck reaching into the treetops, smaller dinosaurs by a lake behind',
   motion='the brachiosaurus moves its long neck slowly and chews leaves, takes a heavy step, the smaller dinosaurs walk along the shore, ferns sway',
   around='jungle and lake around, ferns below, sky above'),
 'jurassic_swamp_v2': dict(
   front='an active prehistoric volcanic landscape, an erupting volcano with lava fountains and glowing lava rivers, black volcanic rock, a triceratops walking across the cooled lava field',
   motion='lava fountains erupt and lava rivers flow and glow, ash and smoke billow upward, the triceratops walks slowly, embers drift',
   around='volcanic land around, black lava rock below, a red ash-filled sky above'),
 'jurassic_beach_v1': dict(
   front='a prehistoric coastline with strong waves breaking on a sandy beach, black volcanic rocks, pterosaurs flying over the surf, tree ferns behind the beach',
   motion='waves roll in and crash with white foam and spray, the pterosaurs glide along the surf, ferns sway in the sea wind',
   around='primitive jungle behind, sand below, a hazy sky above'),
 'jurassic_beach_v2': dict(
   front='a prehistoric sandy coast with rolling waves, a herd of large dinosaurs walking along the shoreline, pterosaurs in the sky',
   motion='the dinosaurs walk slowly along the wet sand with heavy natural steps, waves wash over the sand, the pterosaurs glide',
   around='coast and jungle around, sand below, sky above'),
 # ---------------- medieval / fantasy ----------------
 'great_hall_v1': dict(
   front='a grand medieval great hall with a long feast table, a roaring fireplace, knights and ladies in medieval clothing seated and talking at the table, a minstrel playing a lute',
   motion='the people eat, raise goblets and gesture naturally while talking, the minstrel strums the lute, the fire crackles, candle flames flicker',
   around='stone walls with tapestries around, a stone floor below, wooden beams and chandeliers above'),
 'great_hall_v2': dict(
   front='a gothic cathedral interior with stained glass windows casting colored light, a few people kneeling in prayer in the pews, an ornate golden music box on a stand in the foreground, candles',
   motion='the music box cylinder turns slowly, the people pray and bow their heads gently, candle flames flicker, colored light beams shift',
   around='columns and pews around, stone floor below, ribbed vaults above'),
 'medieval_library_v2': dict(
   front='a vast library built inside a giant ancient forest tree, spiral wooden bookshelves along the trunk, glowing lanterns, an elf with long hair reading at a desk, another elf climbing a ladder',
   motion='the elves turn pages and move naturally, leaves drift down from above, lanterns flicker, fireflies float',
   around='shelves inside the tree all around, wooden floor below, branches and leaves above', ko='숲속 도서관'),
 'lantern_festival_v1': dict(
   front='a calm lake at night with several wooden boats floating, people on the boats releasing a moderate number of glowing paper lanterns, a traditional pavilion on the shore',
   motion='the boats drift slowly, people release lanterns that rise gently into the sky, reflections shimmer on the water',
   around='lake and pavilion around, a wooden pier below, a starry sky with lanterns above'),
 'lantern_festival_v2': dict(
   front='a busy traditional asian night market street with rows of red lanterns, many people in casual and traditional clothes strolling, food stalls with steam',
   motion='people walk and browse naturally, lanterns sway, steam rises from the stalls, vendors cook',
   around='shops around, a stone street below, lanterns above'),
 # ---------------- city ----------------
 'city_night_view_v2': dict(
   front='a beautiful old riverside city at night with a large illuminated double-deck iron arch bridge, colorful historic houses on the hillside, boats on the river',
   motion='lights shimmer and reflect on the river, a tram crosses the bridge, boats glide slowly, people walk along the riverside',
   around='riverside city around, a riverside promenade below, a deep blue night sky above'),
}
assert len(R) == 47, len(R)
GENERIC = ('All motion is natural, continuous and physically plausible: plants, flowers and leaves sway in the breeze, water flows and ripples, '
           'fire and candles flicker; animals, vehicles and people move with realistic natural gait and timing. The camera does not move.')
