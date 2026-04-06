# AvatarCore Bridge Event Queue Checklist

- Check session create, heartbeat, snapshot, and close together.
- Validate both queue directions.
- Preserve explicit missing-session behavior.
- Keep drain limits bounded.
- Close with a real session-and-drain proof.
