# pcb2gcode
A python script which takes a KiCAD PCB file and create the gcode for drilling and routing on a CNC

This is work in progress.

The objectives are:
1. To Create a standalone Python script capable of generating the gcode for the various machining ops for a PCB
2. To have the script usable as a KiCAD plugin
3. To use the script on a CNC with an on-board CPU supporting Python (Typically, a Linux system)

The machining operations for a PCB are:
1. Hole cutting for PTH
   This includes drilling holes, cutting slots, and oblong holes (drill or route) prior to platting the holes
2. Contours routing and NPTH holes
   The contour routing is the final step and is IMHO always combined with the drilling and slot cutting of non-platted holes
3. Engraving
   I have no need for this one personnaly as I etch chemically. But I can see may poeple being interested in this

The engraving creates the need for further operations, such as:
1. Mesh levelling
   This is a tough one. On some CNC (Masso), the mesh level is created by running the G38.6 gcode, which write the position to a file.
   So, this step requires creating a gcode - then processing the output file, to finally create the final GCode
2. PCB positioning
   This one would allow the operator to position the PCB on the machining table (orientation, position, scale)
   This step is also important for hole machining operations in post processing (once a PCB has been etched)

The initial effort are to create an object framework to be able to manage the machining.

The following concepts are introduced:
 * A machining **Session** is created from an **Inventory** which derives from a PCB file.
 Since the CNC could be processing other things than a PCB, the session represents what steps are required.
 The **Session** creates **Job**s. Each **Job** is a single step.
 Independently, a **StockRoom** is created, which holds all fixtures and cutting tools. These are **StockItems**,
 and range from **CuttingTool** such as **DrillBit** or **RouterBit**, but also **BackPlate** which are all **Consumables**,
 but also **MachiningPlate**, and various **Fixtures** such as **LocatingHole** or **PositioningBracket** or **EdgeDetector**.

 Since the script could be run in different environment, the idea is to create a framework to start with with enough
 flexibility to allow various operations to take place, but without constraining the final objective.

Example: The rack.
The rack is typically created for a job - or - a set of jobs - and would primarily benefit a CNC with ATC.
For the concept should also hold true for a manual tool change, where the operator should be made aware
of all the tools required for the Job(s) before starting.
A missing tool could be replaced. A hole can be drilled - but also routed.
Any routing could be done with smaller bits and more passes.
The final rendering of the job as GCode will be constrained by some of the fixtures such as the backing board
which may limit the size of some of the drillbits. (Typical drillbit have a angled shape which require some clearance than in some
case exceeds the backing board thickness).
So the rack object will start from some rack definition files, and could be modified later on.
If the rack has fewer slots than required or if the operator decides to minimize tool changes, the GCode rendering will change.

So, the coding started too fast, there is a need to go back to defining the use cases, then the architecture, then the code.


