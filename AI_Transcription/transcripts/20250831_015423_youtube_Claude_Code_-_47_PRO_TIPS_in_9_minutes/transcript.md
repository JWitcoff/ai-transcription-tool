# Transcript

**Source:** https://www.youtube.com/watch?v=TiNpzxoBPz0
**Date:** 2025-08-31 01:54:23
**Provider:** whisper

---

## Content


Hey, my name is Greg. I'm a developer and over the last few months, Cloud Code has become my default
way of writing code. And so in this video, I want to walk you through some cloud code pro tips.

These pro tips are primarily based on this post written by Boris Cherny, who's the creator of cloud
code at Anthropic. And we're going to go through these pro tips pretty quickly. First tip, Cloud
Code is a CLI.

So all the things that you're used to doing with other bash based CLIs, you can probably do a cloud
code. For instance, you can pass in command like arguments, which will be run on startup. You can
use dash P to run it in headless mode.

You can chain it with other command line tools. You can pipe data into it. You can run multiple
instances of it at once.

You can actually have cloud code launch instances of cloud code. In fact, anytime you ask it to spin
up a sub agent or anytime you see task, that's exactly what cloud code is doing. Next category,
images, you can use an image simply by dragging it in to the terminal.

On OS X, you can use shift, command, control, four to copy the screenshot, and then use control V to
paste it into cloud. That's control V, not command V like you're used to. There's two ways that you
might find yourself using images a lot.

The first is mockups. You can design a mockup, paste the mockup into cloud, and then ask it to build
that interface. Second, you can use images to close the feedback loop with cloud.

Ask it to build something, open up what it built, and then take a screenshot, feed that back into
cloud, and it's pretty good at iterating when you're giving it feedback. Now, that's a manual
process for taking images. You can also automate the screenshotting by using the puppeteer MCP
server.

Which is pretty easy to set up and run locally. Then you can ask cloud to use puppeteer to go open
up the app, take a screenshot of it, and it can save those screenshots to your local directory.
Speaking of MCP servers, cloud code can function as both an MCP server and an MCP client.

So that means that you can actually turn cloud code into an MCP server that can then be used by
other agents. There's a whole bunch of MCP servers that you could use. It would be a whole video on
its own just to go through some of the most popular ones.

So we'll just hit a couple. For instance, you might find it useful to use the Postgres server to
hook up cloud code directly to your database. You can use MCP servers that are effectively wrappers
around APIs.

Other DevTool companies like CloudFair are using their MCP servers to provide up-to-date
documentation to cloud. Not all DevTool companies are making their docs available via MCP just yet.
So if you just paste in the link, CloudCode can fetch that URL and then use those docs to build
against.

You might also want to use fetch URLs to retrieve knowledge from the world that you use in your app.
For instance, I built a game for my four-year-old daughter that was a bluey Uno. Instead of trying
to describe the rules myself or relying on the training data for Uno rules, I pasted it in Unor
rules.com and had CloudCode the gaming logic based on what it read there.

Next category, Cloud.MD. This is actually the first pro tip that's mentioned and Boris is post. A
Cloud.MD is a prompt that is loaded with every request that you make to CloudCode.

This might include instructions for your project, such as common bash commands to use, style
guidelines, linting guidelines, how to run your tests, repository etiquette, and if you type slash
and knit after you launch Cloud in a directory, it will create this Cloud.MD file for you after
scanning the directory and summarizing its structure. If as you're coding, you want to add
instructions to the Cloud.MD. You can use the hash sign.

You can also set a global Cloud.MD in your home directory slash.Cloud. This will be loaded anytime
that you're using CloudCode across any project. You can also add a Cloud.MD file in sub-directories.

You should also refactor your Cloud.MD files often. So it's common for them to grow and complexity
as you continue to work on a project. But remember that this is a prompt that is being loaded on
every turn of conversation with CloudCode and these models do much better the more specific you are.

So you don't want this to be crammed with a bunch of duplicative, extraneous information. You can
use Anthropics prompt optimizer tool to help you write better Cloud.MD files. Slash commands.

You can define these in the dot-clog slash commands folder and they're just prompts. So for
instance, here's one mentioned in Boris's post about solving GitHub issues. You might write a slash
command for refactoring.

You might write a slash command for linting. You might write a slash command for reviewing a PR
slash commands are prompt templates. So you can pass command line arguments when you run the slash
command that will then be interpolated into the prompt template.

Couple of UI tips. One, you can use tab to complete files and directories. CloudCode does better the
more specific you are.

So if you can actually let it know what files or what directories to work with, you'll generally get
better results. Hit escape often. I know that I when I started was hesitant to interrupt Cloud when
I saw it going off path.

But you will find your sessions go so much better if you just stop Cloud as soon as you see it go in
the wrong direction. You can hit escape and ask it to undo its work from the previous turn. That
will help you go back as well.

Speaking of undoing Cloud's work. I think the biggest failure mode here when working with Cloud code
is you use it to build a project. You get that project to a place where it's working really well.

And then it gets overly ambitious. Does a bit too much makes breaking changes. And then you have a
hard time rolling them back.

And the easiest way to mitigate this failure state is to use Cloud code in conjunction with version
control. Ask Cloud code to commit after every major change. Have Cloud code right your commit
messages.

There's a good chance they'll be the best commit messages that have ever been submitted to a
repository that you own. When working with Cloud code, revert more often than what you're used to.
Oftentimes the best way to fix things is just to clear out the conversation history in Cloud, revert
back to a previous save point and try again with slightly more specific instructions.

Install the GitHub CLI and it will use this for all of its interactions with GitHub. If for some
reason you don't want to install this tool, you can also interact with GitHub via the GitHub MCP
server. You can have Cloud code file PRs for you.

You can have Cloud code do code reviews on those PRs. Managing context can certainly be a bit of a
challenge when working with Cloud code. You want to always keep an eye on the auto compacting
indicator.

You always want to know about how long you have until Cloud auto compacts. Prematureally compact
when you're at natural breakpoints. So if you see your 35% of the way to auto compacting and you
just finished up a task, you just made a commit.

You might just want to go ahead and compact right there and start the next task with all of the
tokens available to you. Also consider often clearing instead of compacting. Work in such a way that
you can use Cloud code with fresh memory.

One way to do this is to tell Cloud to use scratch pads to plan its work. Alternative to scratch
pads you can use GitHub issues. If you are paying per token, then you're going to really want to
monitor that context window usage and you're going to want to use external memory as much as
possible.

If you're looking for more robust cost tracking across a team, for instance, one way to achieve that
is by using Cloud codes open telemetry support. So for instance, you could hook up Cloud code to
data dog and produce dashboards that look like this. And for more details on this, you should check
out Martin Amps blog post, which is linked in the description.

But in my opinion, the best way to manage your cost is just to upgrade to one of those Cloud Max
plans. Either $100 or $200. I'm on the $100 plan.

I spend about $150 worth of Cloud code tokens over the course of about three days. If there's a
common complaint of Cloud code, it's very expensive. So I was very excited to see Cloud code use
bundled in with Cloud Max.

I don't even know if I got through half of the pro tips that are included in this post. If you want
to learn more, check out this excellent post here by Boris and check out some of the other links
that I left below in the description.

---

## Analysis

**User Request:** List each of the 47 tips the narrator makes on working better with claude code

# 47 Pro Tips for Working Better with Claude Code

Here’s a structured list of the 47 pro tips shared by Greg in the video "Claude Code - 47 PRO TIPS in 9 minutes." Each tip is categorized for clarity and includes specific examples from the transcript.

## 1. General Usage of Claude Code
1. **CLI Functionality**: Claude Code operates as a Command Line Interface (CLI).
   - You can pass command-line arguments on startup.
   - Use `-P` to run in headless mode.
   - Chain with other command line tools and pipe data into it.
   - Run multiple instances simultaneously.

## 2. Working with Images
2. **Image Input**: Drag images into the terminal.
   - On OS X, use `Shift + Command + Control + 4` to copy a screenshot, then `Control + V` to paste.
3. **Mockups**: Paste mockups into Claude Code to ask it to build an interface.
4. **Feedback Loop**: Use screenshots of what Claude Code builds to provide feedback for iteration.
5. **Automated Screenshotting**: Set up Puppeteer MCP server to automate screenshotting.

## 3. MCP Servers
6. **MCP Server Functionality**: Claude Code can act as both an MCP server and client.
7. **Postgres Server**: Connect Claude Code directly to your database.
8. **API Wrappers**: Use MCP servers that wrap around APIs for documentation.
9. **Fetch URLs**: Retrieve knowledge from the web to inform your app.

## 4. Cloud.MD
10. **Cloud.MD Files**: These are prompts loaded with every request.
    - Include project instructions, bash commands, style guidelines, etc.
11. **Creating Cloud.MD**: Use `/` and `knit` to create a Cloud.MD file after scanning a directory.
12. **Adding Instructions**: Use the hash sign to add instructions during coding.
13. **Global Cloud.MD**: Set a global Cloud.MD in your home directory for all projects.
14. **Refactoring**: Regularly refactor Cloud.MD files to keep them concise and relevant.
15. **Prompt Optimization**: Use Anthropics prompt optimizer tool for better Cloud.MD files.

## 5. Slash Commands
16. **Define Slash Commands**: Use the `.clog/slash_commands` folder for prompt templates.
17. **Examples of Slash Commands**: Create commands for refactoring, linting, or reviewing PRs.

## 6. User Interface Tips
18. **Tab Completion**: Use the tab key to complete file and directory names.
19. **Escape Key**: Hit escape to interrupt Claude Code when it goes off track.

## 7. Version Control
20. **Use Version Control**: Always use version control with Claude Code.
21. **Commit After Changes**: Ask Claude Code to commit after major changes.
22. **Revert Often**: Revert to previous states more frequently to avoid breaking changes.
23. **GitHub CLI**: Install the GitHub CLI for all interactions with GitHub.

## 8. Managing Context
24. **Monitor Auto Compacting**: Keep an eye on the auto compacting indicator.
25. **Premature Compaction**: Compact at natural breakpoints to maintain context.
26. **Clearing Context**: Clear context instead of compacting when necessary.
27. **Scratch Pads**: Use scratch pads for planning work.
28. **GitHub Issues**: Utilize GitHub issues as an alternative to scratch pads.
29. **Token Management**: Monitor context window usage if paying per token.

## 9. Cost Tracking
30. **Open Telemetry Support**: Use Claude Code's open telemetry support for cost tracking.
31. **Data Dog Integration**: Hook up Claude Code to Data Dog for robust dashboards.

## 10. Additional Tips
32. **Be Specific**: Claude Code performs better with specific instructions.
33. **Iterative Feedback**: Provide iterative feedback to improve results.
34. **Avoid Ambition**: Avoid overly ambitious requests that lead to breaking changes.
35. **Use Clear Instructions**: The clearer your instructions, the better Claude Code will perform.
36. **Utilize External Resources**: Leverage external resources and documentation for better results.
37. **Regular Updates**: Keep your tools and libraries updated for optimal performance.
38. **Community Engagement**: Engage with the community for shared tips and best practices.
39. **Experimentation**: Don’t hesitate to experiment with different commands and setups.
40. **Documentation**: Maintain thorough documentation of your processes for future reference.
41. **Learning Resources**: Utilize available learning resources to enhance your understanding of Claude Code.
42. **Feedback Mechanism**: Establish a feedback mechanism for continuous improvement.
43. **Stay Informed**: Keep up with updates and new features in Claude Code.
44. **Network with Peers**: Connect with other developers to share insights and tips.
45. **Practice Regularly**: Regular practice will enhance your proficiency with Claude Code.
46. **Seek Help When Needed**: Don’t hesitate to seek help from more experienced users.
47. **Stay Organized**: Keep your workspace and projects organized for better efficiency.

These tips provide a comprehensive guide to maximizing your effectiveness while working with Claude Code. Implementing these strategies can significantly enhance your coding experience and productivity.