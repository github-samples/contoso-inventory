---
applyTo: "services/**/*.java"
description: This file describes instructions for Java code style and best practices for the project.
---

- Follow standard naming conventions — Classes in PascalCase, methods/variables in camelCase, constants in UPPER_SNAKE_CASE, packages in lowercase. 
- Program to interfaces, not implementations — Declare variables/parameters using the most general interface type (e.g., List<String> list = new ArrayList<>()) to enable flexibility and loose coupling. 
- Favor composition over inheritance — Prefer delegating to component objects rather than extending classes; inheritance breaks encapsulation and creates fragile hierarchies. 
- Handle exceptions properly — Never swallow exceptions with empty catch blocks, use checked exceptions for recoverable conditions and runtime exceptions for programming errors, and always clean up resources with try-with-resources.
- Adhere to SOLID principles — Especially Single Responsibility (one reason to change per class) and Dependency Inversion (depend on abstractions); foundational for maintainable OO design. 
- Make classes immutable whenever possible — Mark fields private final, avoid setters, and don't expose internal mutable state; immutable objects are inherently thread-safe and easier to reason about. 