"""
Friction Stir Welding (FSW) geometry generator for ANSYS Workbench / Fluent
Creates a STEP CAD file containing:
  - Plate_1 and Plate_2 (butt joint at x = 0)
  - Tool_Shoulder
  - Tool_Pin

Units: mm
Requirements: Python + Gmsh Python API
Run:  python fsw_geometry_gmsh.py

Import the generated FSW_geometry.step into ANSYS Workbench > Geometry
(SpaceClaim or DesignModeler), then create named selections and mesh.
"""

import gmsh
import os

# ---------------------- USER-EDITABLE PARAMETERS ----------------------
PLATE_LENGTH = 200.0       # along welding direction, Y (mm)
PLATE_TOTAL_WIDTH = 100.0  # across joint, X (mm)
PLATE_THICKNESS = 5.0      # Z (mm)

SHOULDER_DIAMETER = 20.0   # (mm)
SHOULDER_THICKNESS = 5.0  # (mm)
PIN_DIAMETER = 6.0        # (mm)
PIN_LENGTH = 4.5          # penetration into workpiece (mm)

# Tool position along the weld line. The seam is x=0.
# Keep this within -PLATE_LENGTH/2 to +PLATE_LENGTH/2.
TOOL_Y_POSITION = -50.0

OUTPUT_STEP = "FSW_geometry.step"

# ---------------------- GEOMETRY CREATION ----------------------------
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 1)
gmsh.option.setNumber("Geometry.Tolerance", 1e-5)
gmsh.model.add("Friction_Stir_Welding")

occ = gmsh.model.occ

half_L = PLATE_LENGTH / 2.0
half_W = PLATE_TOTAL_WIDTH / 2.0
half_plate_width = PLATE_TOTAL_WIDTH / 2.0

# Two plates meet at x=0 to form a butt joint.
plate1 = occ.addBox(
    -half_W, -half_L, 0,
    half_plate_width, PLATE_LENGTH, PLATE_THICKNESS
)
plate2 = occ.addBox(
    0, -half_L, 0,
    half_plate_width, PLATE_LENGTH, PLATE_THICKNESS
)

# Tool axis is located directly above the butt-joint line (x=0).
# Shoulder rests on the top surface of the plates.
shoulder_z = PLATE_THICKNESS
shoulder = occ.addCylinder(
    0, TOOL_Y_POSITION, shoulder_z,
    0, 0, SHOULDER_THICKNESS,
    SHOULDER_DIAMETER / 2.0
)

# Pin extends down from the shoulder into the workpiece.
pin = occ.addCylinder(
    0, TOOL_Y_POSITION, PLATE_THICKNESS - PIN_LENGTH,
    0, 0, PIN_LENGTH,
    PIN_DIAMETER / 2.0
)

occ.synchronize()

# Physical groups provide useful labels in the Gmsh mesh.
volumes = gmsh.model.getEntities(3)
volume_map = {tag: [] for dim, tag in volumes}

def find_volume_near(x, y, z):
    """Find the volume whose bounding-box centre is nearest the target point."""
    best_tag, best_dist = None, float("inf")
    for dim, tag in gmsh.model.getEntities(3):
        xmin, ymin, zmin, xmax, ymax, zmax = gmsh.model.getBoundingBox(dim, tag)
        cx, cy, cz = (xmin+xmax)/2, (ymin+ymax)/2, (zmin+zmax)/2
        d = (cx-x)**2 + (cy-y)**2 + (cz-z)**2
        if d < best_dist:
            best_tag, best_dist = tag, d
    return best_tag

# Add named physical volumes. The STEP file contains separate CAD solids.
for tag in [plate1, plate2, shoulder, pin]:
    if (3, tag) in gmsh.model.getEntities(3):
        pass

pg = gmsh.model.addPhysicalGroup(3, [plate1])
gmsh.model.setPhysicalName(3, pg, "Plate_1")
pg = gmsh.model.addPhysicalGroup(3, [plate2])
gmsh.model.setPhysicalName(3, pg, "Plate_2")
pg = gmsh.model.addPhysicalGroup(3, [shoulder])
gmsh.model.setPhysicalName(3, pg, "Tool_Shoulder")
pg = gmsh.model.addPhysicalGroup(3, [pin])
gmsh.model.setPhysicalName(3, pg, "Tool_Pin")

# Mesh settings for an optional first-pass tetrahedral mesh.
gmsh.option.setNumber("Mesh.MeshSizeMin", 1.0)
gmsh.option.setNumber("Mesh.MeshSizeMax", 5.0)
gmsh.option.setNumber("Mesh.Algorithm3D", 1)

# Export CAD and mesh.
gmsh.write(OUTPUT_STEP)
gmsh.model.mesh.generate(3)
gmsh.write(OUTPUT_MSH)

print("\nFSW geometry generated successfully:")
print("  STEP:", os.path.abspath(OUTPUT_STEP))
print("  MSH: ", os.path.abspath(OUTPUT_MSH))
print("\nImport FSW_geometry.step into ANSYS Workbench.")
print("Note: The pin/shoulder intentionally intersect the workpiece.")
print("For CFD, define the tool as a rotating wall and the workpiece")
print("using the material/rheology model appropriate to your FSW study.")

gmsh.finalize()
