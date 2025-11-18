from procurement_bot import parse_more_category

def test_parse_more_category_basic():
    assert parse_more_category('更多工程類') == '工程類'
    assert parse_more_category('更多工程') == '工程類'
    assert parse_more_category('更多財物類') == '財物類'
    assert parse_more_category('更多勞務') == '勞務類'
    assert parse_more_category('隨便問') is None


if __name__ == '__main__':
    test_parse_more_category_basic()
    print('parse_more_category tests passed')
