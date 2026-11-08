# Accessibility

The overlay exposes accessible names for close, provider, progress, response, error, follow-up input, and send controls. Standard Qt keyboard focus and Enter-to-send behavior are preserved. Provider and monitoring state are expressed as text, not color alone.

Release review checks Windows screen-reader labels, keyboard traversal, high-contrast readability, 200% display scaling, visible focus, error announcement, and cancellation without a mouse. Offscreen CI verifies the accessible-name contract but does not replace manual assistive-technology testing.
