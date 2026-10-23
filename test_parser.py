from app.parser import parse_text, flatten

def test_duplicate_headings_stay_distinct_and_parented():
    roots=parse_text('1 Root\n1.1 Duplicate\nbody a\n1.2 Other\n1.3 Duplicate\nbody b')
    children=roots[0].children
    assert len(children)==3
    assert children[0].heading==children[2].heading
    assert children[0] is not children[2]
    assert all(c.level==2 for c in children)

def test_out_of_order_numbering_uses_stack_parenting():
    roots=parse_text('1 Root\n1.1 Child\n1.1.1 Grandchild\n1.2 Sibling\n2 Next')
    assert roots[0].children[0].children[0].heading.startswith('1.1.1')
    assert roots[0].children[1].heading.startswith('1.2')
    assert roots[1].level==1

def test_stray_marker_and_unformatted_body_are_retained():
    roots=parse_text('1 Root\nA paragraph split across lines\n-\ncontinued text')
    assert 'A paragraph' in roots[0].body[0]
    assert '-' in roots[0].body
    assert 'continued text' in roots[0].body
