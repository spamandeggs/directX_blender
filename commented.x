xof 0303txt 0032

Header {
1;
0;
1;
}

// Definition of Mesh
//{ nVertices (DWORD); vertices[1]...vertices[nVertices] (Vector);
// nFaces (DWORD); faces[1]...faces[nFaces] (MeshFace); }


Mesh CubeMesh {
8; // 8 vertices
1.000000;1.000000;-1.000000;, // vertex 0
-1.000000;1.000000;-1.000000;, // vertex 1
-1.000000;1.000000;1.000000;, // etc...
1.000000;1.000000;1.000000;,
1.000000;-1.000000;-1.000000;,
-1.000000;-1.000000;-1.000000;,
-1.000000;-1.000000;1.000000;,
1.000000;-1.000000;1.000000;;

12; // 12 faces
3;0,1,2;, // face 0 has 3 vertices
3;0,2,3;, // etc...
3;0,4,5;,
3;0,5,1;,
3;1,5,6;,
3;1,6,2;,
3;2,6,7;,
3;2,7,3;,
3;3,7,4;,
3;3,4,0;,
3;4,7,6;,
3;4,6,5;; // <- note that we put ;; indicates the end of a containter!
}