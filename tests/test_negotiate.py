# -*- coding: utf-8 -*-
# Copyright: (c) 2020, Jordan Borean (@jborean93) <jborean93@gmail.com>
# MIT License (see LICENSE or https://opensource.org/licenses/MIT)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type  # noqa (fixes E402 for the imports below)

import pytest
import spnego

from spnego._context import (
    GSSMech,
)

from spnego._spnego import (
    NegState,
    NegTokenResp,
)

from spnego.exceptions import (
    InvalidTokenError,
)


def test_token_rejected(ntlm_cred):
    c = spnego.client(ntlm_cred[0], ntlm_cred[1], options=spnego.NegotiateOptions.use_negotiate)

    c.step()
    token_resp = NegTokenResp(neg_state=NegState.reject).pack()

    with pytest.raises(InvalidTokenError, match="Received SPNEGO rejection with no token error message"):
        c.step(token_resp)


def test_token_acceptor_first(ntlm_cred):
    c = spnego.client(ntlm_cred[0], ntlm_cred[1], options=spnego.NegotiateOptions.use_negotiate)
    s = spnego.server(options=spnego.NegotiateOptions.use_negotiate)

    assert c._mech_list == []
    assert s._mech_list == []

    token1 = s.step()
    assert isinstance(token1, bytes)
    assert not c.complete
    assert not s.complete
    assert c._mech_list == []
    assert s._mech_list == [GSSMech.ntlm.value]

    negotiate = c.step(token1)
    assert isinstance(negotiate, bytes)
    assert not c.complete
    assert not s.complete
    assert c._mech_list == [GSSMech.ntlm.value]
    assert s._mech_list == [GSSMech.ntlm.value]

    challenge = s.step(negotiate)
    assert isinstance(challenge, bytes)
    assert not c.complete
    assert not s.complete

    authenticate = c.step(challenge)
    assert isinstance(authenticate, bytes)
    assert not c.complete
    assert not s.complete

    mech_list_mic = s.step(authenticate)
    assert isinstance(mech_list_mic, bytes)
    assert not c.complete
    assert s.complete

    final_token = c.step(mech_list_mic)
    assert final_token is None
    assert c.complete
    assert s.complete
