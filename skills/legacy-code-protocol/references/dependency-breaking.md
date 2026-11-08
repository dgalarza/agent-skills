# Dependency-Breaking Techniques

Moves that get code into a test harness with the least risk. Choose one from the symptom in [symptoms.md](symptoms.md), and apply it under the [pre-test edit rules](../SKILL.md#pre-test-edits). When none of these fits, use another technique from the dependency-breaking catalog in *Working Effectively with Legacy Code*.

## Seams

A **seam** is a place where behavior can be changed without editing the code at that place. Its **enabling point** is where you choose which behavior runs.

| Seam | Enabling point | Typical use |
|------|----------------|-------------|
| Object seam | Which object is passed in, constructed, or subclassed | Most work in OO and dynamic languages |
| Link seam | Which implementation the build, linker, module loader, or import path resolves | Module mocking in JS and Python, load-path swaps in Ruby, classpath swaps in Java |
| Preprocessing seam | Macros and conditional compilation | C and C++ only |

Prefer object seams. They show up in the code, and the next reader can see where substitution happens.

## Parameterize Constructor

**Use when:** a constructor creates a collaborator internally, such as a database client, an HTTP client, or a clock.

1. Add a constructor parameter for the collaborator, defaulting to the object it creates now. In languages without default arguments, keep the old constructor and have it delegate to a new one that takes the parameter.
2. Assign the parameter where the object was created before.
3. In tests, pass a fake.

**Risk:** low. In a language with overloading, an ambiguous overload can resolve to a different constructor. Lean on the compiler.

## Parameterize Method

**Use when:** a method creates a collaborator inline, and only that method needs it.

Add a parameter for the collaborator, defaulting to what the method creates now, or keep the old signature delegating to the new one. Callers stay unchanged.

**Risk:** low. Watch for callers that pass positional arguments past the new parameter.

## Extract Interface

**Use when:** a test needs to substitute a concrete class it can't construct, and the language uses nominal types (Java, C#, TypeScript classes used as types, and similar).

1. Declare an interface with the methods the code under test calls on that class.
2. Make the concrete class implement it.
3. Change the code under test to depend on the interface.
4. In tests, write a fake that implements the interface.

**Risk:** low with a compiler. In duck-typed languages, skip this step and pass any object that responds to the same methods.

## Extract and Override Call

**Use when:** a method makes one problem call, such as sending an email, charging a card, or reading the clock.

1. Move the call into a new method on the same class with the same arguments. It should be protected or overridable.
2. In tests, subclass and override that method to record the call or return a fixed value.

**Risk:** low. It is the smallest seam when the call sits in the middle of a long method.

## Extract and Override Factory Method

**Use when:** a constructor creates a collaborator, and the constructor's signature has to stay unchanged.

Move the creation into an overridable factory method, and override it in a testing subclass.

**Risk:** in languages that dispatch virtually during construction differently from ordinary calls (C++ calls the base version from inside a constructor), this technique does not work. Use Parameterize Constructor there.

## Subclass and Override Method

**Use when:** the behavior to remove or sense lives in a method of the class under test.

Make the method overridable if needed. In tests, subclass and override it with a version that does nothing, records the call, or returns a fixed value. Many of the other techniques build on this one.

**Risk:** the override must not drop behavior the test depends on. Override the narrowest method that isolates the dependency.

## Adapt Parameter

**Use when:** a method takes a parameter type that is hard to construct or fake, such as a framework request object, and only reads a little from it.

1. Define a small type that exposes only what the method uses.
2. Write an adapter from the real type to the small type.
3. Change the method to take the small type, with callers wrapping their argument in the adapter.

**Risk:** this one changes a signature. Keep the adapter a pure pass-through and lean on the compiler for every caller.

## Break Out Method Object

**Use when:** a long method uses many local variables and instance fields, and it can't be tested in place.

1. Create a class whose constructor takes the original object and the method's arguments.
2. Move the method body into a method on the new class, unchanged. Reach back through the original object for the fields it used.
3. Have the original method build the new object and call it.

After this, the method object can be characterized and its body split into smaller methods under test.

**Risk:** medium. Accessing fields through the original object can change visibility rules. Lean on the compiler.

## Encapsulate Global References

**Use when:** code reads or writes global variables or module-level state.

Move the related globals into a class or module, and route access through it. Tests then supply a fresh instance.

**Risk:** global state shared across tests produces order-dependent failures. Reset it in setup, not in teardown alone.

## Replace Global Reference with Getter

**Use when:** a class references a global or singleton in many places.

Replace each direct reference with a call to an overridable getter on the class. Override the getter in a testing subclass.

**Risk:** low. Every reference has to go through the getter. Search for any that were missed.

## Introduce Static Setter

**Use when:** code reaches a singleton through a static accessor, and the singleton can't be passed in.

Add a static setter that replaces the singleton instance, test-only by convention, and reset it after every test. If the singleton's constructor is private, make it protected so a test subclass can exist.

**Risk:** the setter is a back door. Mark it for test use, and reset it reliably, because a leaked fake will break unrelated tests.

## Expose Static Method

**Use when:** the method to test uses no instance state, but the class is hard to construct.

Make the method static, or extract its body into a static function the instance method delegates to, and test it directly.

**Risk:** low. Confirm the method reads no instance fields. The compiler will tell you in typed languages.

## Pass Null

**Use when:** a constructor or method demands an argument that is hard to build, and the code path under test never uses it.

In a test, pass `null`, `nil`, or `None`. If the code does use it, the test fails loudly, which shows the dependency is real.

**Risk:** use it only in tests, and only in languages that fail loudly on null access.

## Dynamic languages

In Ruby, Python, and JavaScript, these are often the lightest object seams:

- **Keyword arguments with defaults** for collaborators. This is Parameterize Constructor or Parameterize Method in one line.
- **Duck-typed fakes** in place of Extract Interface.
- **Module-level stubbing** through the test framework's own tools, such as RSpec doubles, `unittest.mock.patch`, or `jest.mock`. This is a link seam. Use it when the code reaches a module directly and an object seam would mean a wider edit. Patch the public name the code under test reaches, so the test does not couple to private internals.
