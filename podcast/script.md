# Priced Out: The $712 Nobody Talks About

**Episode script — AIPI-510 Module Project 1**
Hosts: Natalie Zachariah (NZ) and Haydn Stucker (HS)
Target runtime: 18–20 minutes

> Production note: every figure cited here is printed by `python src/eda.py`.
> Timestamps are estimates for pacing.

---

## COLD OPEN (0:00–1:15)

**NZ:** I want to start with two numbers, and I want you to guess which one is
the scandal.

Between 2021 and 2023, the price of the typical American home went up eleven
percent.

**HS:** Okay. That's bad, but it's not shocking. Prices go up.

**NZ:** Right. Here's the second number. Over those exact same two years, the
monthly payment on that exact same typical house went up **fifty-four percent**.

**HS:** Fifty-four.

**NZ:** Same house. Same two years. The price went up eleven percent and the
cost of owning it went up fifty-four.

**HS:** So where does the other forty-three points come from?

**NZ:** That's the episode.

*[THEME]*

**HS:** I'm Haydn Stucker.

**NZ:** I'm Natalie Zachariah. This is a story about why buying a house stopped
working for people our age — and about how the explanation everyone reaches for
first turns out to be wrong.

---

## ACT ONE — The wrong question (1:15–4:30)

**HS:** So let's set this up. When people talk about the housing crisis, what do
they actually talk about?

**NZ:** Prices. Almost always prices. "Homes cost too much." And that's true —
the median home sold for about $383,000 in 2021 and roughly $419,000 in 2024.

**HS:** But here's the thing we kept running into. Nobody pays a price.

**NZ:** Say more.

**HS:** Unless you're paying cash, you don't pay $419,000. You pay a monthly
payment, every month, for thirty years. And that payment doesn't just depend on
the price. It depends on the price **and** the interest rate, multiplied
together.

**NZ:** And those two things moved in completely different directions.

**HS:** Completely. So the first thing we did with this data wasn't to plot
prices. It was to build the payment. We took the median home price, assumed a
standard conventional loan — twenty percent down, thirty-year fixed — used the
actual average mortgage rate for that year, and added property taxes and
insurance.

**NZ:** Basically: what does the bank actually take out of your account on the
first of the month.

**HS:** Exactly. And when you chart the price and the payment side by side, they
stop moving together around 2021 and just... split apart.

*[FIGURE: 02_price_vs_payment.png]*

**NZ:** So put the payment in dollars for me.

**HS:** In 2021, the payment on the median home was about **$1,843 a month**. By
2023 it was **$2,845**.

**NZ:** That's a thousand dollars a month.

**HS:** A thousand and two, and that's about **twelve thousand dollars a year**
— for the same house.

---

## ACT TWO — The surprise (4:30–9:00)

**NZ:** Okay, so this is where the analysis got interesting, because we could
have stopped there. But "the payment went up" still doesn't tell you *why*.

**HS:** Right, and we could see two suspects. Prices went up. Rates went up.
Which one actually did the damage?

**NZ:** And you can't just eyeball that, because they're tangled together.

**HS:** So we ran a counterfactual. Which sounds fancy but is genuinely simple:
we asked the data two "what if" questions.

**NZ:** Question one.

**HS:** What if prices had risen exactly as they did — but mortgage rates had
never moved off their 2021 level? What's the payment then?

**NZ:** And question two is the mirror image.

**HS:** What if rates had risen exactly as they did — but prices had frozen at
2021? Whatever's left over, we report separately, because payments don't split
perfectly cleanly.

**NZ:** And the answer.

**HS:** Of that thousand-dollar-a-month increase: about **$209** came from
higher prices. That's twenty-one percent.

**NZ:** And rates?

**HS:** **$712 a month.** Seventy-one percent of the entire increase.

**NZ:** So the thing everyone talks about — prices — is the small piece.

**HS:** It's roughly a fifth of it. And the further out you go, the more lopsided
it gets, because prices have actually drifted *down* from their peak while rates
stayed high. In the 2026 data so far, rates account for seventy-nine percent.

*[FIGURE: 03_payment_decomposition.png]*

**NZ:** I want to sit on that, because it reframes the whole conversation. If the
problem is prices, the fix is "build more houses" and you wait a decade. If the
problem is the rate, the same house becomes affordable or unaffordable based on
a decision made in a conference room in Washington.

**HS:** And it means two people who bought the identical house three years apart
have wildly different lives. Not because one of them was smarter or more
disciplined. Because of when they signed.

---

## ACT THREE — "So young people just earn too little" (9:00–13:00)

**NZ:** Okay, so here's where I have to admit something. Going in, I had a
hypothesis, and I was pretty confident about it.

**HS:** Which was?

**NZ:** That young people's incomes had fallen behind. That's the story you hear
constantly — wages stagnated, young people earn less than their parents did,
that's why they can't buy.

**HS:** And we could actually test that, because the Census publishes median
income broken out by the age of the person who heads the household.

**NZ:** So what's the median income for a household headed by someone 25 to 34?

**HS:** In 2024, **$90,100**.

**NZ:** And the median for *all* American households?

**HS:** **$83,730**.

**NZ:** So young households earn *more*.

**HS:** About eight percent more than the typical American household.

**NZ:** Which — I want to be honest — was the opposite of what I expected.

**HS:** And there's a mundane reason for it. The all-ages median includes
retirees, who mostly aren't earning wages anymore. So it gets pulled down.
Households in their late twenties and thirties are near their earning peak.

**NZ:** So the "young people don't earn enough" explanation just isn't what the
data says.

**HS:** It's not. And it gets sharper. From 2021 to 2023, the median young
household got a **fourteen and a half percent raise**. In two years.

**NZ:** That's a good raise.

**HS:** That's a great raise. And over those same two years, the income a bank
would *require* to approve you for the median home went from about **$79,000 to
$122,000**.

**NZ:** Fifty-four percent.

**HS:** So you got a fourteen percent raise, and the bar moved fifty-four
percent. You ran faster and the finish line moved further.

*[FIGURE: 01_income_vs_required.png]*

**NZ:** Explain how you get "required income," because that's an engineered
number — that's not something you download.

**HS:** Right, we built it. Lenders use a rule of thumb where your housing
payment shouldn't exceed about twenty-eight percent of your gross income. So we
ran that rule backwards: take the monthly payment, multiply by twelve, divide by
twenty-eight percent. That's the income you need to walk in the door.

**NZ:** And then you turned that into an index.

**HS:** Yeah — the median young household's income divided by that required
income. A hundred means the typical young household exactly qualifies for the
typical house. Below a hundred means they don't.

**NZ:** And where are we?

**HS:** In 2020, it was **104**. Young households could — just barely — afford
the median home. By 2023 it was **70**.

**NZ:** In three years.

**HS:** In three years.

*[FIGURE: 04_affordability_index.png]*

---

## ACT FOUR — The honest objection (13:00–16:00)

**NZ:** Now. I want to do the thing where we argue against ourselves, because
when we showed this to people, one objection came up every single time.

**HS:** Let's hear it.

**NZ:** "Mortgage rates were eighteen percent in the eighties. My parents dealt
with way worse. Isn't this generation just soft?"

**HS:** And I want to be straight with people: on the measure we just built,
that objection is **correct**.

**NZ:** Really.

**HS:** In 1984, mortgage rates averaged almost fourteen percent. Our
affordability index for that year is **63.8**. In 2024 it's **75.6**. By the
monthly-payment test, 1984 was harder than today.

**NZ:** So why are we still making this episode?

**HS:** Because the monthly payment is only half the wall. There's a second
barrier that measure completely misses, and it's the one that actually stops
people.

**NZ:** The down payment.

**HS:** The down payment. We asked: if you save ten percent of your gross income
every year, how long does it take to save twenty percent of the median home?

**NZ:** And in 1984?

**HS:** **6.7 years.**

**NZ:** And now?

**HS:** **9.3 years.** Nearly three extra years of saving — and that's *before*
rent, which is the thing eating the money you'd be saving.

*[FIGURE: 06_years_to_down_payment.png]*

**NZ:** There's a second thing that objection misses, and it's about what
happened *next*.

**HS:** Right. If you bought in 1984 at fourteen percent, rates fell for the next
forty years. You refinanced. That high rate was temporary and you had an exit.

**NZ:** And someone signing at six and a half percent today has no guarantee of
that.

**HS:** None. They might get one. But it's a hope, not a plan.

**NZ:** And I think the fair way to say all of this is: it's not that today is
uniformly worse than 1984. It's that the *shape* of the barrier changed. It used
to be the monthly payment. Now it's the pile of cash you need before anyone will
even talk to you.

---

## ACT FIVE — Does any of it show up? (16:00–18:00)

**HS:** So the last thing we wanted to check: is this all theoretical? Or do you
actually see it in whether people own homes?

**NZ:** And this is the number that got me.

**HS:** In 1994, the homeownership rate for households under 35 was **37.4
percent**. It peaked in 2004 at **43.1 percent**. Today it's **36.0 percent**.

**NZ:** Lower than 1994.

**HS:** Lower than 1994. Three decades, and young people are slightly *less*
likely to own a home than they were before most of them were born.

*[FIGURE: 05_homeownership_by_age.png]*

**NZ:** And the gap between young households and everyone else is about
twenty-nine points, which is wider than it was in the nineties.

---

## LIMITATIONS (18:00–19:15)

**NZ:** Before we land this, we owe you the caveats, because we made choices and
those choices shaped the answer.

**HS:** Biggest one: the buyer in this analysis doesn't exist. We modeled a
conventional loan with twenty percent down at the national median price. Real
people put three and a half percent down with an FHA loan, or get help from
family, or buy something cheaper than the median.

**NZ:** And there's no such thing as a national housing market. Austin and
Cleveland are different planets. These numbers are a pressure gauge over time,
not a forecast for your city.

**HS:** Second: we used medians, and medians hide who's actually buying. If the
pool of buyers shifts toward wealthier people, the median can look calm while
access quietly narrows underneath it.

**NZ:** And the one I think matters most — we treated "young people" as one
group. That flattens the biggest inequity in American housing. Homeownership
rates differ enormously by race, and the Black-white homeownership gap is wider
now than when housing discrimination was still legal.

**HS:** And that connects directly to the down payment finding, because
down-payment money is very often *inherited*. It comes from parents who already
owned. So a barrier made of accumulated cash doesn't hit everyone equally — it
compounds whatever your family already had.

**NZ:** Our age-only analysis can't see any of that. It's a real limit, and we
don't want anyone walking away thinking "young people" are one thing.

**HS:** Last one: everything we showed is arithmetic, not causation. We showed
that rate increases *account for* the payment jump. We're not explaining why the
Fed did what it did, and none of this is financial advice.

---

## CLOSE (19:15–20:00)

**NZ:** So what do you want people to take away?

**HS:** That if you're in your late twenties or thirties and you feel like you're
doing everything right and it still isn't working — the data is on your side.
You probably *did* get a raise. Young households out-earn the typical American
household. And it still got harder, fast, because the bar moved more than three
times as fast as your income did.

**NZ:** And that the number to watch isn't the one in the headline. Home prices
are down from their peak. That sounds like good news, and it mostly isn't,
because the payment is still driven by the rate.

**HS:** Seven hundred and twelve dollars a month. That's the piece nobody's
talking about.

**NZ:** All our code and data is public — link in the show notes. You can rerun
every number in this episode with one command, and if you think we chose the
wrong assumptions, change them and see what happens. We'd genuinely like to know.

**HS:** Thanks for listening.

*[OUTRO]*

---

## Appendix: numbers cited

| Claim | Value | Source |
|---|---|---|
| Median price 2021 → 2023 | $383,000 → $426,525 (+11.4%) | FRED `MSPUS` |
| Mortgage rate 2021 → 2023 | 2.96% → 6.80% | FRED `MORTGAGE30US` |
| Monthly payment 2021 → 2023 | $1,843 → $2,845 (+54.4%) | engineered `monthly_piti` |
| Annual payment increase | ~$12,029/yr | engineered |
| Decomposition of +$1,002/mo | prices $209 (21%), rates $712 (71%), interaction $81 (8%) | `payment_decomposition.csv` |
| Rate share, 2026 YTD | 79% | `payment_decomposition.csv` |
| Median income, age 25–34, 2024 | $90,100 | Census CPS H-10 |
| Median income, all households, 2024 | $83,730 | Census CPS H-10 |
| Income 25–34, 2021 → 2023 | $74,860 → $85,780 (+14.6%) | Census CPS H-10 |
| Required income 2021 → 2023 | $78,987 → $121,948 (+54.4%) | engineered `required_income` |
| Affordability index 2020 / 2023 / 2024 | 104.3 / 70.3 / 75.6 | engineered |
| Affordability index 1984 | 63.8 (rate 13.9%) | engineered |
| Years to save 20% down, 1984 → 2024 | 6.7 → 9.3 | engineered |
| Homeownership under 35: 1994 / 2004 / 2026 | 37.4% / 43.1% / 36.0% | Census HVS Table 19 |
| Under-35 gap vs all ages, 2026 | 29.2 points | Census HVS Table 19 |

*2026 values are year-to-date averages through August 2026.*
