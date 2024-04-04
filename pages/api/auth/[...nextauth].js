import { connectDB } from "../../../util/database";
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { MongoDBAdapter } from "@next-auth/mongodb-adapter";

export const authOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        phoneNumber: { label: "Phone Number", type: "text" },
        password: { label: "Password", type: "password" },
      },
      
      async authorize(credentials) {
        let db = (await connectDB).db('test');
        let user = await db.collection('user').findOne({ username: credentials.phoneNumber });

        if (!user) {
          console.log('해당 전화번호는 없음');
          return null;
        }

        // bcrypt.compare 대신 단순 문자열 비교를 사용합니다.
        if (credentials.password !== user.password) {
          console.log('비밀번호 틀림');
          return null;
        }

        console.log('로그인 성공');
        return user;
      }
    })
  ],

  // 세션 및 콜백 설정은 동일하게 유지됩니다.
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60
  },

  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        token.user = {};
        token.user.name = user.name;
        token.user.phoneNumber = user.phoneNumber; 
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
