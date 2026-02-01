#!/bin/bash
for i in {131..140}; do
  slug=$(yq ".levels.\"b2-hist\".modules[$((i-1))]" curriculum/l2-uk-en/curriculum.yaml)
  echo "Module $i ($slug):"
  has_meta=$(test -f curriculum/l2-uk-en/b2-hist/meta/${slug}.yaml && echo "META: YES" || echo "META: NO")
  has_lesson=$(test -f curriculum/l2-uk-en/b2-hist/${slug}.md && echo "LESSON: YES" || echo "LESSON: NO")
  has_activities=$(test -f curriculum/l2-uk-en/b2-hist/activities/${slug}.yaml && echo "ACT: YES" || echo "ACT: NO")
  has_vocab=$(test -f curriculum/l2-uk-en/b2-hist/vocabulary/${slug}.yaml && echo "VOCAB: YES" || echo "VOCAB: NO")
  echo "$has_meta | $has_lesson | $has_activities | $has_vocab"
done
