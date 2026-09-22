How we work

Tasks
Every task is a GitHub issue with a label, one person assigned, and a milestone. Milestones follow the course sessions (Session 04, Session 05, Mid-sem on October 6, and so on). The board has four columns: Todo, In Progress, In Review, Done.

Branches and pull requests
Each issue gets its own branch, named after the area and the task, like data/data-sources or eng/voice-loop. Nobody pushes straight to main, and branch protection wouldn't let us anyway. Every pull request says Closes #N so it's linked to its issue, and someone other than the author reviews and approves it before it's merged. No approving your own work, and no merging a few seconds after opening the PR.

Our week
Friday: quick check-in in the group chat about what's done and what's stuck.
Monday: everyone adds their own line to the weekly report draft.
Tuesday by noon: the report pull request is open.
Tuesday by 4pm: the report is approved and merged. The deadline is 5pm Eastern, and we don't want to cut it close.
Before the report goes in
The file is reports/sessionNN.md with a two-digit number, and it's on main.
Every claim links to an issue, pull request or commit.
Every one of us has our own line with our own evidence.
"What did not work" has something real in it.
Any number we report comes from the model that's actually running.
When something counts as done
When it's merged to main or deployed, and its issue is closed. Nearly done doesn't count.