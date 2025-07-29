#!/usr/bin/env python3
"""
Simple dependency visualization script for dependency analysis results.

Creates ASCII-based visualizations of module dependencies and architecture.

Copyright (c) 2024 Yesman Claude Project
Licensed under the MIT License
"""

import json
from collections import defaultdict
from pathlib import Path


def load_analysis_data(file_path: Path) -> dict:
    """Load dependency analysis data from JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_dependency_tree(data: dict, root_module: str, max_depth: int = 3) -> None:
    """Create ASCII tree visualization of dependencies."""
    print(f"\n🌳 DEPENDENCY TREE for {root_module}")
    print("=" * 60)

    modules = data["modules"]
    if root_module not in modules:
        print(f"Module {root_module} not found!")
        return

    def print_tree(module: str, depth: int = 0, visited: set = None, prefix: str = ""):
        if visited is None:
            visited = set()

        if depth > max_depth or module in visited:
            return

        visited.add(module)

        # Print current module
        if depth == 0:
            print(f"{module}")
        else:
            print(f"{prefix}├── {module}")

        # Get dependents
        dependents = modules.get(module, {}).get("dependents", [])

        # Sort dependents for consistent output
        dependents = sorted(dependents)

        # Print dependents
        for i, dependent in enumerate(dependents):
            if depth + 1 <= max_depth:
                is_last = i == len(dependents) - 1
                new_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(dependent, depth + 1, visited.copy(), new_prefix)

    print_tree(root_module)


def create_layer_diagram(data: dict) -> None:
    """Create ASCII diagram showing architectural layers."""
    print("\n🏗️ ARCHITECTURAL LAYERS")
    print("=" * 60)

    # Categorize modules by layer
    layers = {"API Layer": [], "Commands Layer": [], "Core Services": [], "Dashboard": [], "Utilities": []}

    for module in data["modules"].keys():
        if module.startswith("api."):
            layers["API Layer"].append(module)
        elif module.startswith("commands."):
            layers["Commands Layer"].append(module)
        elif module.startswith("libs.core."):
            layers["Core Services"].append(module)
        elif module.startswith("libs.dashboard."):
            layers["Dashboard"].append(module)
        elif module.startswith("libs."):
            layers["Utilities"].append(module)

    # Calculate dependencies between layers
    layer_deps = defaultdict(set)

    for module, info in data["modules"].items():
        module_layer = None
        for layer, modules in layers.items():
            if module in modules:
                module_layer = layer
                break

        if module_layer:
            for dep in info["dependencies"]:
                for layer, modules in layers.items():
                    if dep in modules and layer != module_layer:
                        layer_deps[module_layer].add(layer)

    # Print layer diagram
    print("┌─────────────────────────────────────────────────────────┐")
    print("│                     API Layer                           │")
    print(f"│  {len(layers['API Layer'])} modules (REST endpoints, WebSocket, etc.)        │")
    print("└─────────────────────────────────────────────────────────┘")
    print("                            │")
    print("                            ▼")
    print("┌─────────────────────────────────────────────────────────┐")
    print("│                  Commands Layer                         │")
    print(f"│  {len(layers['Commands Layer'])} modules (CLI commands, multi-agent ops)     │")
    print("└─────────────────────────────────────────────────────────┘")
    print("                            │")
    print("                            ▼")
    print("┌─────────────────────────────────────────────────────────┐")
    print("│                  Core Services                          │")
    print(f"│  {len(layers['Core Services'])} modules (base classes, session mgmt)       │")
    print("└─────────────────────────────────────────────────────────┘")
    print("                         │      │")
    print("            ┌────────────┘      └──────────────┐")
    print("            ▼                                  ▼")
    print("┌─────────────────────┐         ┌─────────────────────────┐")
    print("│     Dashboard       │         │      Utilities         │")
    print(f"│   {len(layers['Dashboard'])} modules        │         │     {len(layers['Utilities'])} modules          │")
    print("│  (UI, widgets, etc) │         │  (config, utils, etc)  │")
    print("└─────────────────────┘         └─────────────────────────┘")


def create_coupling_analysis(data: dict) -> None:
    """Show coupling analysis and problematic modules."""
    print("\n⚖️ COUPLING ANALYSIS")
    print("=" * 60)

    high_coupling = data["high_coupling_modules"]

    # Categorize by coupling issues
    highly_unstable = [m for m in high_coupling if m["instability"] > 0.8]
    highly_distant = [m for m in high_coupling if m["distance"] > 0.7]

    print("🔴 HIGHLY UNSTABLE MODULES (Instability > 0.8):")
    if highly_unstable:
        for module in highly_unstable[:5]:
            print(f"  • {module['module']}")
            print(f"    Instability: {module['instability']:.2f} | Efferent: {module['efferent_coupling']} | Afferent: {module['afferent_coupling']}")
    else:
        print("  None found ✅")

    print("\n🟡 HIGH DISTANCE FROM MAIN SEQUENCE (Distance > 0.7):")
    if highly_distant:
        for module in highly_distant[:5]:
            print(f"  • {module['module']}")
            print(f"    Distance: {module['distance']:.2f} | Instability: {module['instability']:.2f}")
    else:
        print("  None found ✅")

    # Fan-out analysis
    most_dependent = data["most_dependent_modules"][:5]
    print("\n📤 HIGHEST FAN-OUT (Most Dependencies):")
    for module in most_dependent:
        print(f"  • {module['module']}: {module['dependency_count']} dependencies")

    # Fan-in analysis
    most_depended = data["most_depended_upon_modules"][:5]
    print("\n📥 HIGHEST FAN-IN (Most Dependents):")
    for module in most_depended:
        print(f"  • {module['module']}: {module['dependent_count']} dependents")


def create_hotspot_analysis(data: dict) -> None:
    """Identify architectural hotspots and potential issues."""
    print("\n🔥 ARCHITECTURAL HOTSPOTS")
    print("=" * 60)

    modules = data["modules"]

    # Find God objects (high fan-in + high LOC)
    god_objects = []
    for module, info in modules.items():
        dependents = len(info["dependents"])
        loc = info["lines_of_code"]
        if dependents > 5 and loc > 200:
            god_objects.append((module, dependents, loc))

    god_objects.sort(key=lambda x: x[1] * x[2], reverse=True)

    print("👑 POTENTIAL GOD OBJECTS (High dependents + High LOC):")
    if god_objects:
        for module, dependents, loc in god_objects[:3]:
            print(f"  • {module}")
            print(f"    Dependents: {dependents} | LOC: {loc}")
    else:
        print("  None found ✅")

    # Find feature envy (modules with many external dependencies)
    feature_envy = []
    for module, info in modules.items():
        dependencies = len(info["dependencies"])
        if dependencies > 5:
            feature_envy.append((module, dependencies))

    feature_envy.sort(key=lambda x: x[1], reverse=True)

    print("\n🤝 POTENTIAL FEATURE ENVY (High external dependencies):")
    if feature_envy:
        for module, deps in feature_envy[:3]:
            print(f"  • {module}: {deps} dependencies")
    else:
        print("  None found ✅")

    # Find unused modules (no dependents, minimal dependencies)
    unused = []
    for module, info in modules.items():
        if len(info["dependents"]) == 0 and len(info["dependencies"]) <= 1:
            unused.append(module)

    print(f"\n💤 POTENTIALLY UNUSED MODULES ({len(unused)} found):")
    if unused:
        for module in sorted(unused)[:5]:
            print(f"  • {module}")
        if len(unused) > 5:
            print(f"  ... and {len(unused) - 5} more")
    else:
        print("  None found ✅")


def main():
    """Main visualization function."""
    import argparse

    parser = argparse.ArgumentParser(description="Visualize dependency analysis results")
    parser.add_argument("--input", "-i", type=Path, default=Path("dependency_analysis.json"), help="Input JSON file from dependency analysis")
    parser.add_argument("--tree", "-t", type=str, help="Show dependency tree for specific module")
    parser.add_argument("--layers", "-l", action="store_true", help="Show architectural layers")
    parser.add_argument("--coupling", "-c", action="store_true", help="Show coupling analysis")
    parser.add_argument("--hotspots", "-h", action="store_true", help="Show architectural hotspots")
    parser.add_argument("--all", "-a", action="store_true", help="Show all visualizations")

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input file {args.input} not found!")
        print("Run dependency_graph_analyzer.py first to generate the analysis data.")
        return

    data = load_analysis_data(args.input)

    print("🔍 YESMAN-CLAUDE DEPENDENCY VISUALIZATION")
    print("=" * 60)
    print(f"📄 Data from: {args.input}")
    print(f"📊 Modules: {data['summary_statistics']['total_modules']}")
    print(f"🔗 Dependencies: {data['summary_statistics']['total_internal_dependencies']}")

    if args.all or args.layers:
        create_layer_diagram(data)

    if args.all or args.coupling:
        create_coupling_analysis(data)

    if args.all or args.hotspots:
        create_hotspot_analysis(data)

    if args.tree:
        create_dependency_tree(data, args.tree)

    if not any([args.tree, args.layers, args.coupling, args.hotspots, args.all]):
        print("\n💡 Use --help to see visualization options")
        print("   Example: python dependency_visualizer.py --all")
        print("   Example: python dependency_visualizer.py --tree libs.core.base_command")


if __name__ == "__main__":
    main()
