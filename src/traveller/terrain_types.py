from traveller.terrain import Terrain

mountain = Terrain(
	symbols=["^", "⧍", "∧", "Λ", "⋀", "/\\", "/^\\", "⎠⎝"],
	spread=2,
	min_density=0.1,
	max_density=0.35
)

forest = Terrain(
	symbols="♣♠⧪♤⧭⫛♧⧬⚲ϕ↟⇑↥⏃↑⚴",
	spread=1,
	min_density=0.2,
	max_density=0.45
)

hills = Terrain(
	symbols="⁀⁔〰⏜⩋∩⋂",
	spread=2,
	min_density=0.1,
	max_density=0.35
)

plains = Terrain(
	symbols="⥾,`\"'⁀⁔",
	spread=2,
	min_density=0.1,
	max_density=0.2
)

desert = Terrain(
	symbols=".⥎⬞⁀⁔㇃㇀⊓∏",
	spread=2,
	min_density=0.05,
	max_density=0.25
)

sea = Terrain(
	symbols="﹏﹋﹏﹋﹏﹋﹏﹋∩﹏﹋﹏﹋﹏﹋﹏﹋﹏﹋﹏﹋﹏﹋﹏﹋﹏﹋﹏﹋﹏﹋",
	#symbols="～〜~〰",
	spread=7,
	min_density=0.5,
	max_density=1
)