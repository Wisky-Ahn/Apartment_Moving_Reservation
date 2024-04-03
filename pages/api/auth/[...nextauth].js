import { connectDB } from "../../../util/database";
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import bcrypt from 'bcrypt';
import { MongoDBAdapter } from "@next-auth/mongodb-adapter";

export const authOptions = {
  providers: [
    CredentialsProvider({
      // 1. 로그인 페이지 폼에서 전화번호를 사용합니다.
      name: "Credentials",
      credentials: {
        phoneNumber: { label: "Phone Number", type: "text" },
        password: { label: "Password", type: "password" },
      },
      
      // 2. 로그인 요청 시 실행되는 코드
      // DB에서 전화번호와 비밀번호를 비교합니다.
      async authorize(credentials) {
        let db = (await connectDB).db('test');
        let user = await db.collection('user').findOne({ username: credentials.phoneNumber });
        if (!user) {
          console.log('해당 전화번호는 없음');
          return null;
        }
        const pwCheck = await bcrypt.compare(credentials.password, user.password);
        if (!pwCheck) {
          console.log('비밀번호 틀림');
          return null;
        }
        console.log('로그인 성공');
        return user;
      }
    })
  ],

  // 3. JWT 설정 및 만료 기간
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60 // 30일
  },

  // JWT 생성 및 세션 관련 콜백 함수
  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        token.user = {};
        token.user.name = user.name;
        token.user.phoneNumber = user.phoneNumber; // 이메일 대신 전화번호를 저장
      }
      return token;
    },
    session: async ({ session, token }) => {
      session.user = token.user;
      return session;
    },
  },

  adapter: MongoDBAdapter(connectDB),
  secret: 'qwer1234'  
};

export default NextAuth(authOptions);

// import { connectDB } from "../../../util/database";
// import NextAuth from "next-auth";
// import CredentialsProvider from "next-auth/providers/credentials";
// import bcrypt from 'bcrypt';
// import { MongoDBAdapter } from "@next-auth/mongodb-adapter";

// export const authOptions = {
//   providers: [
//     CredentialsProvider({
//       name: "Credentials",
//       credentials: {
//         username: { label: "Username", type: "text", placeholder: "jsmith" },
//         password: { label: "Password", type: "password" },
//       },
//       async authorize(credentials, req) {
//         const db = await (await connectDB).db();
//         const user = await db.collection('users').findOne({ username: credentials.username });

//         if (user && bcrypt.compareSync(credentials.password, user.password)) {
//           // email을 참조하는 코드를 제거합니다.
//           return { id: user.id, name: user.name };
//         }

//         // 로그인 실패 시 null을 반환합니다.
//         return null;
//       },
//     }),
//   ],

//   callbacks: {
//     async signIn({ user, account, profile, credentials }) {
//       // 로그인 성공 또는 실패 시 반환 값이 여기서 결정됩니다.
//       return !!user;
//     },
//     async redirect({ url, baseUrl }) {
//       // 사용자가 로그인에 성공하면 메인 페이지로 리디렉션됩니다.
//       return baseUrl;
//     },
//     async session({ session, token }) {
//       // 세션 정보에서 필요한 부분만 저장합니다.
//       if (token) {
//         session.id = token.id;
//         session.name = token.name;
//       }
//       return session;
//     },
//     async jwt({ token, user }) {
//       // JWT 토큰 생성 시 필요한 정보를 저장합니다.
//       if (user) {
//         token.id = user.id;
//         token.name = user.name;
//       }
//       return token;
//     },
//   },
//   pages: {
//     signIn: '/logins/login',
//     error: '/logins/login',
//   },
//   adapter: MongoDBAdapter(connectDB),
//   secret: process.env.SECRET,
// };

// export default NextAuth(authOptions);
