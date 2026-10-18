from sonar_app.desktop_terms import ensure_runtime_terms


def test_terms_decline_accept_and_changed_terms(tmp_path):
    root = tmp_path / 'resources'
    terms = root / 'THIRD_PARTY_NOTICES/supplemental/Microsoft-WebView2-Fixed-Runtime.html'
    terms.parent.mkdir(parents=True)
    terms.write_text('original terms')
    user = tmp_path / 'user'; user.mkdir()
    assert not ensure_runtime_terms(user, root, lambda _: 7, lambda _: None)
    assert not (user / 'webview2-terms.json').exists()
    answers = iter([2, 6]); opened = []
    assert ensure_runtime_terms(user, root, lambda _: next(answers), opened.append)
    assert opened == [str(terms)]
    def unexpected(_):
        raise AssertionError('Accepted unchanged terms must not prompt again')
    assert ensure_runtime_terms(user, root, unexpected, opened.append)
    terms.write_text('updated terms')
    assert not ensure_runtime_terms(user, root, lambda _: 7, opened.append)
