# Domain-Driven Architecture Guide

This guide explains the domain-driven design (DDD) principles applied in UCore and how they shape the UCoreFrameworck's structure and extensibility.

---

## What is Domain-Driven Design (DDD)?

Domain-Driven Design is an approach to software development that emphasizes modeling software to match a business domain, using clear boundaries and language.

---

## DDD in UCore

- **Domains as Modules:** Each major concern (core, data, messaging, etc.) is a separate domain/module in `UCoreFrameworck/`.
- **Bounded Contexts:** Each domain has clear boundaries and responsibilities.
- **Ubiquitous Language:** Consistent terminology across code, docs, and APIs.
- **Entities & Components:** Core logic is encapsulated in components and entities, supporting OOP and extensibility.
- **Event-Driven:** Domains communicate via events, not tight coupling.

---

## Example: Domain Separation

- `UCoreFrameworck/core`: App orchestration, DI, plugins, config
- `UCoreFrameworck/data`: Persistence, DB, cache, ODM
- `UCoreFrameworck/messaging`: EventBus, distributed messaging
- `UCoreFrameworck/resource`: Resource lifecycle, pooling, health

---

## Extending with DDD

- Add new domains as new subdirectories in `UCoreFrameworck/`
- Use events for cross-domain communication
- Keep domain logic isolated and testable

---

## Benefits

- Clear separation of concerns
- Easier to extend and maintain
- Scalable for large projects

---

## See Also

- [Project Structure Guide](project-structure-guide.md)
- [UCore Framework Guide](ucore-UCoreFrameworck-guide.md)
