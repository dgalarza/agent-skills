# Symptoms

Start from what blocks you, then go to the technique. Techniques are described in [dependency-breaking.md](dependency-breaking.md).

## Getting a class or function into the harness

| Symptom | First move | Alternatives |
|---------|------------|--------------|
| The constructor does I/O or builds collaborators | Parameterize Constructor | Extract and Override Factory Method |
| The constructor needs an argument that is hard to build, and the path under test never uses it | Pass Null | Extract Interface, or a duck-typed fake |
| A method creates a collaborator inline | Parameterize Method | Extract and Override Factory Method |
| A method makes one call with side effects (email, payment, network, clock) | Extract and Override Call | Extract Interface plus a fake |
| The code reaches a global, singleton, or module-level state | Encapsulate Global References | Replace Global Reference with Getter, Introduce Static Setter |
| The dependency lives in a method of the class under test | Subclass and Override Method | Extract and Override Call |
| A parameter type is hard to construct, such as a framework request | Adapt Parameter | Extract Interface |
| The method uses no instance state, but the class is hard to construct | Expose Static Method | Break Out Method Object |
| The code calls a third-party API directly throughout | Wrap the API behind a thin class you own, then fake that class | Module-level stubbing as a link seam |

## Seeing what the code did

| Symptom | First move |
|---------|------------|
| The method returns nothing and writes to a database, file, or network | Fake the collaborator so it records the write |
| The effect is internal state in a long method | Sensing variable |
| The output is large or textual | Golden master |
| The output varies run to run | Pin time, randomness, and IDs first |

These are covered in [characterization-tests.md](characterization-tests.md).

## Shape of the code

| Symptom | First move |
|---------|------------|
| The method is too long to test in place | Break Out Method Object, then characterize its outputs |
| The class is too big, and the change touches one responsibility | Sprout Class for the new logic, and extract the rest later under tests |
| The same change is needed in several places | Sketch effects to find a pinch point, and test there |
| You don't understand the code well enough to change it | **Scratch refactoring:** refactor freely in a separate git worktree or copy to learn the code, then delete that copy and start the real change in the original working tree. Effect sketches and characterization tests also build understanding |
| There's no time to get the change point under test | Sprout Method or Class, or Wrap Method or Class |

## Harness and environment

| Symptom | First move |
|---------|------------|
| No test runner is set up | Propose a minimal runner setup to the user, or Sprout into a new tested unit |
| The test suite is too slow to run often | Run the narrowest subset that covers the change area, and report the full run separately |
| The only way to observe the behavior is end to end | Write one end-to-end characterization test at the pinch point, then break dependencies to get faster tests beneath it |
