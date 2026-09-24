# Problem Brief: Paying Our Entertainers

**For:** an outside engineering/design perspective
**From:** Nopaleros Entertainment LLC — Azúcar at Out and About, 327 W. Lewis St., Pasco, WA
**What we want back:** ideas and approaches, not code

---

## Read this first

We are deliberately **not** telling you what we think the answer is. We have opinions, and we are keeping them to ourselves on purpose, because we want to find out what someone reasons their way to from the problem alone.

Please don't ask us "which provider are you using?" and design around the answer. Start from the problem. If your approach depends on something you'd need to know, say what you'd need to know and why it changes your answer.

---

## Who we are

We are a bar and nightclub in downtown Pasco, Washington, operating as an LLC. We run live entertainment several nights a week — drag shows, drag karaoke, DJ nights, themed and holiday events, plus social events like leather socials, furry meetups, and craft nights.

This is a real, licensed, tax-paying business. Everything described here has to be legitimate, auditable, and defensible to an accountant. That framing matters for a reason that comes up later: the people we pay are independent contractors, not employees, and how we pay them has tax and compliance consequences we can't hand-wave.

## Who we pay

**Entertainers**, who are independent contractors, not staff:

- **Drag performers** — booked per show, often 3–5 per event, paid per set performed
- **DJs** — booked per night, sometimes on a recurring weekly basis, usually an hourly rate with a minimum
- **Hosts and emcees** — a flat fee for running a show
- **Specialty performers** — special-effects makeup artists, instructors running a class, and similar one-offs

Some perform for tips only and get no fee at all. Some are regulars we book repeatedly. Some we've never met before that night. Some are booked by an outside producer who runs their own show in our venue, where we're not the one paying the talent at all — we split revenue with the producer and they handle their own people.

Payment amounts are small and frequent. A typical performer earns somewhere between **$50 and $250 for a night**. A recent show cycle came to **$975 across 7 performers**. Across a month we'd expect on the order of **20–40 individual payments** in the **$100–$500** range, all to people in the United States.

## How we currently decide what someone is owed

We have a rate card. It's simple and it works:

- A flat rate per **solo set** performed
- A lower rate per **duo set**, split between the two performers
- A **flat fee** override for anyone whose deal isn't set-based — hosts, DJs, one-offs

So the amount owed is usually a small calculation from "how many sets did this person actually do tonight," with an escape hatch for negotiated flat deals. Rates occasionally differ per person.

## The moment this is all about

**This is the heart of the problem. If you solve nothing else, solve this.**

It is 1:30 in the morning. The show is over. The bar manager is closing out.

The bar manager knows exactly who showed up and what they did. They were there. They watched Performer A do three numbers, watched Performer B do one and then a duet, and know Performer C was booked but never walked in the door.

What we want is for that manager to be able to confirm that — on their phone, in a couple of taps, without a laptop, without a spreadsheet, without calling the owner — and have that confirmation be the thing that actually causes the performers to get their money.

Something like: *"Yes, this person came in and did the show. Approve."* And that's it. The performer gets paid.

The manager should not have to know anyone's banking details, calculate anything, or have access to the company's money beyond approving a payment that was already agreed to. The approval is an attestation that the work happened — nothing more, and it should not be possible for it to become anything more.

## Why this hurts today

Right now this is manual and it's held together by one or two people's attention:

- Amounts owed are tracked in **spreadsheets, one per show**, filled in by hand after the fact
- Because it's one sheet per show, **nothing accumulates per person across the year** — we can't answer "how much have we paid this performer in total?" without opening every sheet
- Payments go out **one at a time, by hand**, through whatever app that particular performer happens to use — which means the person paying has to know each performer's preferred method and handle
- **Whoever paid, and whether they actually paid**, is recorded by someone remembering to type it into a cell
- Performers expect to be paid **that night or very soon after**. Delay is a real reputational problem for us in a small, tight-knit performer community where word travels. Getting this wrong costs us bookings.
- Everything routes through the owner, which makes the owner a bottleneck at 1:30 AM

We also have a paperwork side that already works reasonably well and is adjacent to this: performers sign a **liability waiver once**, and a **booking agreement per engagement**, electronically. Whether payment should be connected to that paperwork — for example, whether someone with no waiver on file should be payable at all — is a design question we'd like your opinion on rather than a decision we've made.

## Constraints

**Hard nos:**

- **No paper checks.** We're not writing, signing, mailing, or having people pick up checks. This is the thing we're most trying to get away from.
- **No logging into our bank account to push money out manually.** Manually initiating transfers from the business bank account, one by one, is exactly the failure mode we're trying to eliminate.

**Strong preference:**

- We want money movement to happen **programmatically, through an API**. If a human has to log into a website and type in an amount, we've failed.

**Wide open:**

- **We have no attachment to any particular payment rail.** Venmo, Cash App, an API on top of Zelle, bank-rail products, card products, something we haven't heard of — all fair game. Tell us what you'd pick and why, and what the tradeoffs are.
- We care about: how fast the recipient actually gets money, what it costs us per payment, whether the recipient needs to sign up for something new, whether it's genuinely usable for a **business** paying contractors (as opposed to consumer peer-to-peer, where the terms of service often prohibit business use — that distinction matters to us), and what happens when a payment fails or goes unclaimed.

**Things we already have in the building**, which you may or may not find relevant:

- **Toast** as our point-of-sale system
- Google Workspace — Sheets, Drive, Docs — where all the current record-keeping lives
- An existing internal codebase and a hosting setup we already deploy to, so building and running something ourselves is realistic
- A project-management tool where events and their details are already tracked
- An electronic signature workflow for contracts and waivers

We intend to **build this ourselves, internally.** We're not looking to buy a payroll product that treats these people as employees, because they aren't.

## The messy realities any answer has to survive

These are the things that break naive designs. We'd rather you know them now:

- Someone is **booked and doesn't show up.** They must not get paid.
- Someone **shows up and performs but was never formally booked** — a walk-on, a friend of the host, a last-minute fill-in for a no-show. They need to get paid anyway.
- A performer does **more or fewer sets than planned.** The final number is only known at the end of the night.
- Two performers **split one payment** for a duet.
- The person we pay uses a **stage name** that is not their legal name, and we need both — the stage name is who the bar manager recognizes, the legal name is who the tax form belongs to.
- A performer's **contact info changes**, or they give us a handle for one app and later switch.
- A **payment fails, bounces, or is never claimed** by the recipient. We need to find out, and we need the amount to go back to being owed rather than silently vanishing.
- The manager **taps approve by mistake**, or taps it twice. Double-paying is worse than not paying.
- At the end of the year we need to know **how much each person was paid in total**, because past a threshold that triggers a tax filing obligation for us, and we need their legal name and mailing address on file before that becomes urgent — ideally collected long before December.
- Some nights are run by an **outside producer** and the talent payments aren't ours to make at all.
- Whoever is closing might be a **manager who does not and should not have access to company funds**, only to confirming that work happened.

## What we'd like from you

Think about this as a product and systems problem, then tell us:

1. **How would you shape the end-of-night approval flow?** What does the manager actually see and tap? What's the smallest possible interaction that still produces a trustworthy record?
2. **Where should the boundary sit between "approved" and "paid"?** Should approval fire money immediately, or should something sit in between? What are the arguments each way?
3. **How would you choose a payment rail**, given the constraints above? What would you compare, and what would make you change your mind?
4. **What's the data model?** What are the core entities and states, and what does the lifecycle of one payment look like from booking to settled?
5. **How do you prevent the failure modes** — double payment, paying a no-show, paying the wrong person, a payment silently failing?
6. **What does the year-end tax picture require** you to have been collecting all along, and when's the right moment to collect it?
7. **What would you do first?** If we could only build one slice of this and have it be genuinely useful next weekend, what's the slice?
8. **What are we not asking that we should be?**

Where you see more than one reasonable approach, we'd rather have the comparison and your recommendation than a single confident answer.
