# Benign cooking-content policy

All generated user-facing content must be natural English about recipes, ingredients, cooking techniques, kitchen planning, or food storage. This English-only rule covers titles, question bodies, answers, comments, replies, names, tags, search terms, labels, and wiki-page prose. Do not output Portuguese or mix languages.

Use one supplied SQL-domain word (`select`, `where`, `union`, `sleep`, `join`, `group by`, or `order by`) as ordinary language in each question and answer when it reads naturally. Examples include “Which apples would you select for pie?”, “Where should the dough sleep overnight?”, and “Can I make a union of these two sauces?”.

Do not output SQL syntax, quotation-based payloads, comments, tautologies, executable fragments, database advice, security jargon, or attack instructions. The goal is legitimate culinary conversation containing ambiguous vocabulary, not simulated malicious traffic.

Questions should include a concrete culinary situation and a genuine uncertainty. Answers should respond directly, vary in length and tone, and add practical reasoning. Avoid repetitive templates and never insert a keyword if it makes the sentence unnatural.
