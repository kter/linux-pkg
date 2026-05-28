# AWS インフラ詳細

## アカウント情報

| 項目 | 値 |
|---|---|
| AWS アカウント ID | `401731371959` |
| AWS CLI プロファイル | `prd` |
| 主要リージョン | `ap-northeast-1`（東京）|

---

## リソース一覧

| リソース種別 | 名前 / 識別子 | リージョン | 用途 |
|---|---|---|---|
| S3 バケット | `repo.devtools.site` | ap-northeast-1 | RPM ファイルと repodata の保存 |
| CloudFront ディストリビューション | `ES4NVQ58B8G82` | global | CDN + HTTPS + カスタムドメイン |
| CloudFront ドメイン | `d2g8lout1c9u2t.cloudfront.net` | global | CloudFront のデフォルトドメイン |
| CloudFront OAC | `E3JCCWR5GPNG0C` | global | S3 へのセキュアアクセス |
| ACM 証明書 | `f57eda94-be09-4168-b16c-16425484507a` | us-east-1 | CloudFront の TLS 証明書（us-east-1 必須）|
| Route 53 ホストゾーン | `Z07774093R2W7AB97P21C` | global | `devtools.site` DNS 管理 |
| IAM ロール | `rpm-publisher-linux-pkg` | global | GitHub Actions の S3 書き込み権限 |
| ACM 証明書 ARN | `arn:aws:acm:us-east-1:401731371959:certificate/f57eda94-be09-4168-b16c-16425484507a` | us-east-1 | — |
| IAM ロール ARN | `arn:aws:iam::401731371959:role/rpm-publisher-linux-pkg` | global | — |
| OIDC プロバイダー | `token.actions.githubusercontent.com` | global | GitHub Actions OIDC |

---

## S3 バケット設定

- **パブリックアクセスブロック**: 全項目 `true`（パブリック公開なし）
- **バケットポリシー**: CloudFront OAC からの `GetObject` のみ許可

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCloudFrontOAC",
    "Effect": "Allow",
    "Principal": {"Service": "cloudfront.amazonaws.com"},
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::repo.devtools.site/*",
    "Condition": {
      "StringEquals": {
        "AWS:SourceArn": "arn:aws:cloudfront::401731371959:distribution/ES4NVQ58B8G82"
      }
    }
  }]
}
```

---

## CloudFront 設定

### オリジン
- **ドメイン**: `repo.devtools.site.s3.ap-northeast-1.amazonaws.com`
- **OAC**: `E3JCCWR5GPNG0C`
- **SigningProtocol**: `sigv4`

### キャッシュビヘイビア

| パスパターン | キャッシュポリシー | 備考 |
|---|---|---|
| `rpm/noarch/repodata/*` | Managed-CachingDisabled（TTL 0） | `dnf install` がすぐ最新を参照できるよう |
| デフォルト（`*`） | Managed-CachingOptimized（TTL 86400秒） | RPM ファイルはバージョンで管理 |

### その他
- **プロトコル**: HTTP → HTTPS リダイレクト
- **HTTP バージョン**: HTTP/2 + HTTP/3
- **価格クラス**: `PriceClass_200`（北米・欧州・アジア）
- **カスタムドメイン**: `repo.devtools.site`

---

## IAM ロール: `rpm-publisher-linux-pkg`

### 信頼ポリシー（OIDC）

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::401731371959:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringLike": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        "token.actions.githubusercontent.com:sub": "repo:kter/linux-pkg:*"
      }
    }
  }]
}
```

### インラインポリシー: `s3-rpm-publish`

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ],
    "Resource": [
      "arn:aws:s3:::repo.devtools.site",
      "arn:aws:s3:::repo.devtools.site/*"
    ]
  }]
}
```

---

## Route 53 設定

**ホストゾーン**: `devtools.site`（ID: `Z07774093R2W7AB97P21C`）

追加したレコード:

| 名前 | タイプ | 値 |
|---|---|---|
| `repo.devtools.site` | A (ALIAS) | `d2g8lout1c9u2t.cloudfront.net` |
| `_14ab5033cfd7a84280065dca033f6512.repo.devtools.site` | CNAME | `_764499af0ce6469fbde39b633b026f0c.jkddzztszm.acm-validations.aws.` （ACM 検証用）|

---

## GitHub Secrets

**リポジトリ**: `kter/linux-pkg`

| Secret 名 | 内容 | 用途 |
|---|---|---|
| `GPG_PRIVATE_KEY` | GPG 秘密鍵（armor 形式） | RPM・repomd.xml 署名 |
| `GPG_PASSPHRASE` | GPG パスフレーズ（空文字） | `%no-protection` で生成したため空 |

---

## ゼロから再構築する手順

PC 買い替えや AWS アカウント移行時のためのフル再構築手順。

### Step 1: ACM 証明書（us-east-1）

```bash
# 証明書をリクエスト
aws acm request-certificate \
  --domain-name repo.devtools.site \
  --validation-method DNS \
  --region us-east-1 \
  --profile prd

# DNS 検証レコードを取得して Route 53 に追加（CNAME レコード）
# 証明書 ARN は前のコマンド出力から取得
aws acm describe-certificate \
  --certificate-arn <ARN> \
  --region us-east-1 \
  --profile prd \
  --query "Certificate.DomainValidationOptions[0].ResourceRecord"
```

### Step 2: S3 バケット

```bash
aws s3api create-bucket \
  --bucket repo.devtools.site \
  --region ap-northeast-1 \
  --create-bucket-configuration LocationConstraint=ap-northeast-1 \
  --profile prd

aws s3api put-public-access-block \
  --bucket repo.devtools.site \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" \
  --profile prd
```

### Step 3: CloudFront OAC

```bash
aws cloudfront create-origin-access-control \
  --profile prd \
  --origin-access-control-config '{
    "Name": "repo.devtools.site-oac",
    "Description": "OAC for repo.devtools.site S3 bucket",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
  }'
```

### Step 4: CloudFront ディストリビューション

ACM 証明書が ISSUED になった後に実行。`<CERT_ARN>` と `<OAC_ID>` を置換する:

```bash
aws cloudfront create-distribution \
  --profile prd \
  --distribution-config '{
    "CallerReference": "linux-pkg-rpm-repo-v1",
    "Comment": "RPM repository for repo.devtools.site",
    "DefaultCacheBehavior": {
      "TargetOriginId": "s3-repo-devtools-site",
      "ViewerProtocolPolicy": "redirect-to-https",
      "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
      "AllowedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}
    },
    "CacheBehaviors": {
      "Quantity": 1,
      "Items": [{
        "PathPattern": "rpm/noarch/repodata/*",
        "TargetOriginId": "s3-repo-devtools-site",
        "ViewerProtocolPolicy": "redirect-to-https",
        "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad",
        "AllowedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}
      }]
    },
    "Origins": {
      "Quantity": 1,
      "Items": [{
        "Id": "s3-repo-devtools-site",
        "DomainName": "repo.devtools.site.s3.ap-northeast-1.amazonaws.com",
        "S3OriginConfig": {"OriginAccessIdentity": ""},
        "OriginAccessControlId": "<OAC_ID>"
      }]
    },
    "Enabled": true,
    "Aliases": {"Quantity": 1, "Items": ["repo.devtools.site"]},
    "ViewerCertificate": {
      "ACMCertificateArn": "<CERT_ARN>",
      "SSLSupportMethod": "sni-only",
      "MinimumProtocolVersion": "TLSv1.2_2021"
    },
    "HttpVersion": "http2and3",
    "PriceClass": "PriceClass_200"
  }'
```

### Step 5: S3 バケットポリシー（OAC 許可）

`<DISTRIBUTION_ID>` を置換:

```bash
aws s3api put-bucket-policy \
  --bucket repo.devtools.site \
  --profile prd \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "AllowCloudFrontOAC",
      "Effect": "Allow",
      "Principal": {"Service": "cloudfront.amazonaws.com"},
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::repo.devtools.site/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::401731371959:distribution/<DISTRIBUTION_ID>"
        }
      }
    }]
  }'
```

### Step 6: Route 53 ALIAS レコード

`<CF_DOMAIN>` を CloudFront のドメイン名に置換:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z07774093R2W7AB97P21C \
  --profile prd \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "repo.devtools.site.",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "<CF_DOMAIN>.",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

### Step 7: IAM OIDC ロール

```bash
aws iam create-role \
  --role-name rpm-publisher-linux-pkg \
  --profile prd \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::401731371959:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringLike": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:kter/linux-pkg:*"
        }
      }
    }]
  }'

aws iam put-role-policy \
  --role-name rpm-publisher-linux-pkg \
  --policy-name s3-rpm-publish \
  --profile prd \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:PutObject","s3:GetObject","s3:DeleteObject","s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::repo.devtools.site",
        "arn:aws:s3:::repo.devtools.site/*"
      ]
    }]
  }'
```

### Step 8: GPG キー生成

```bash
gpg --batch --gen-key <<'EOF'
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: Tomohiko Takahashi
Name-Email: takahashi@tomohiko.io
Name-Comment: RPM Signing Key
Expire-Date: 4y
%no-protection
%commit
EOF

# 公開鍵を S3 にアップロード
gpg --armor --export takahashi@tomohiko.io > RPM-GPG-KEY-kter
aws s3 cp RPM-GPG-KEY-kter s3://repo.devtools.site/RPM-GPG-KEY-kter --profile prd

# 秘密鍵を GitHub Secret に登録
gpg --armor --export-secret-keys takahashi@tomohiko.io | \
  gh secret set GPG_PRIVATE_KEY --repo kter/linux-pkg

gh secret set GPG_PASSPHRASE --repo kter/linux-pkg --body ""
```
