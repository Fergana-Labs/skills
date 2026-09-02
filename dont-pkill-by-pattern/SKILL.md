---
name: dont-pkill-by-pattern
description: Stop a local development process without killing unrelated apps or another worktree's server. Use whenever an agent is about to run pkill, killall, taskkill by image name, or a ps/grep/xargs kill pipeline. Resolve, inspect, and terminate one exact PID instead.
---

# Don't pkill by pattern

Never terminate processes by name or command-line pattern.

## The incident

A coding agent meant to stop one Next.js server and ran:

```bash
pkill -f "next dev" -l
```

On macOS, the option after the pattern was parsed differently than the agent expected. The command
killed nearly every Electron and Chromium application on the developer's machine, along with other
unrelated processes.

The lesson is not “put the flags in the right order.” The lesson is that broad process matching is
too dangerous for routine development work.

## The rule

Do not use:

- `pkill` or `killall`;
- `taskkill /IM`;
- `ps | grep | awk | xargs kill`; or
- any command that selects termination targets by a broad name, pattern, glob, or unresolved
  variable.

Use an exact PID that has been resolved and inspected immediately before termination. If zero or
multiple candidates remain, stop and identify the target; do not broaden the match.

## Safe process termination

Prefer the PID captured when the process was started. Otherwise, derive it from a resource uniquely
owned by the target, such as its listening port.

Before terminating it, inspect:

- the PID and full command;
- the process's working directory when multiple worktrees may be running; and
- the resource it owns, such as the expected listening port.

For a server on port 3457, a safe inspection sequence on macOS or Linux is:

```bash
lsof -nP -iTCP:3457 -sTCP:LISTEN
ps -p <exact-pid> -o pid=,ppid=,command=
lsof -a -p <exact-pid> -d cwd
```

Only after those checks identify the intended process, terminate that PID:

```bash
kill <exact-pid>
```

Then verify that the process exited and the resource was released. If graceful termination fails,
re-inspect the same PID before escalating the signal; PIDs can be reused.

Never paste a PID from an earlier run, kill every process returned by a query, or assume a familiar
command belongs to the current worktree.
