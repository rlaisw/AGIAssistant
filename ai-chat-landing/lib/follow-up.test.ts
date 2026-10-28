import { describe, expect, it } from "vitest"

import { splitFollowUp } from "./follow-up"

describe("splitFollowUp", () => {
  it("splits a trailing question paragraph off the answer", () => {
    const r = splitFollowUp("Install SQL Server from setup.exe.\n\nFollow the wizard.\n\nWant me to tailor this for a silent install?")
    expect(r.body).toBe("Install SQL Server from setup.exe.\n\nFollow the wizard.")
    expect(r.followUp).toBe("Want me to tailor this for a silent install?")
  })

  it("leaves answers whose last paragraph is not a question untouched", () => {
    const text = "Step one.\n\nStep two ends with a period."
    expect(splitFollowUp(text)).toEqual({ body: text })
  })

  it("does not treat a single-paragraph answer as a follow-up", () => {
    const text = "Want me to just do it?"
    expect(splitFollowUp(text)).toEqual({ body: text })
  })

  it("takes only the last question when several paragraphs end with ?", () => {
    const r = splitFollowUp("What is a backup?\n\nWhy back up nightly?\n\nWant me to write the cron job?")
    expect(r.followUp).toBe("Want me to write the cron job?")
    expect(r.body).toBe("What is a backup?\n\nWhy back up nightly?")
  })

  it("preserves markdown inside the follow-up", () => {
    const r = splitFollowUp("Body text.\n\nWant me to [open the guide](http://x/y)?")
    expect(r.followUp).toBe("Want me to [open the guide](http://x/y)?")
  })

  it("ignores trailing whitespace after the question mark", () => {
    const r = splitFollowUp("Body.\n\nWant me to continue?  ")
    expect(r.followUp).toBe("Want me to continue?")
  })
})
