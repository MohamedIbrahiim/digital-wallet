from django.urls import path

from transactions.apis import (
    WalletDepositView,
    InternalTransferView,
    P2PSendHoldView,
    WalletTransactionHistoryView,
    UserTransactionHistoryView,
    TransactionActionView,
)

urlpatterns = [
    path(
        "wallets/<str:reference_tag>/deposit/",
        WalletDepositView.as_view(),
        name="wallet-deposit",
    ),
    path(
        "transactions/transfer/",
        InternalTransferView.as_view(),
        name="wallet-internal-transfer",
    ),
    path(
        "transactions/send/",
        P2PSendHoldView.as_view(),
        name="wallet-p2p-send-hold",
    ),
    path(
        "wallets/<str:reference_tag>/transactions/",
        WalletTransactionHistoryView.as_view(),
        name="wallet-transactions",
    ),
    path(
        "transactions/", UserTransactionHistoryView.as_view(), name="user-transactions"
    ),
    path(
        "transactions/<str:tx_id>/action/",
        TransactionActionView.as_view(),
        name="tx-action",
    ),
]
